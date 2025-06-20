import logging
import configparser
import os
import time
import warnings
from exchangelib import Credentials, Account, Configuration, IMPERSONATION, UTC_NOW, HTMLBody
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
from exchangelib.items import SEND_TO_ALL_AND_SAVE_COPY
from meet_me import get_meeting_details

# Setup
BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter
warnings.filterwarnings("ignore")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'settings.ini')
USERS_PATH = os.path.join(BASE_DIR, 'config', 'users.txt')

# Load config
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

# Read variables from config
impers_usr = config['EWS']['impers_usr']
impers_pwd = config['EWS']['impers_pwd']
server = config['EWS']['Server']
magic_word = config['EWS']['magic_w']
log_level = config['Logging']['log_level'].upper()

# Template path: strip leading slashes
inv_template_rel_path = config['EWS']['inv_template'].lstrip('/\\')
TEMPLATE_PATH = os.path.join(BASE_DIR, inv_template_rel_path)

# Log files
MEETINGS_LOG_FILE = os.path.join(BASE_DIR, config['Logging'].get('Meetings_log_file', 'logs/meetings.log'))
SUBSCRIPTION_LOG_FILE = os.path.join(BASE_DIR, config['Logging'].get('Sub_log_file', 'logs/subscriptions.log'))

# Configure main logger (for meetings)
logging.basicConfig(filename=MEETINGS_LOG_FILE, 
    level=getattr(logging, log_level), 
    format='%(asctime)s - %(levelname)s - %(message)s')

# Configure separate logger for subscription errors
subscription_logger = logging.getLogger('subscription')
subscription_logger.setLevel(getattr(logging, log_level))
sub_fh = logging.FileHandler(SUBSCRIPTION_LOG_FILE)
sub_fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
if not subscription_logger.hasHandlers():
    subscription_logger.addHandler(sub_fh)

credentials = Credentials(username=impers_usr, password=impers_pwd)
ews_config = Configuration(server=server, credentials=credentials, auth_type=None)

seen_ids = set()
failed_mailbox_users = set()
service_start_time = UTC_NOW()

while True:
    try:
        with open(USERS_PATH, 'r') as f:
            lines = f.read().splitlines()[1:]  # skip timestamp line
            users = [line.strip() for line in lines if line.strip()]

        for email in users:
            # Skip if previously failed with "no mailbox" error
            if email in failed_mailbox_users:
                continue

            try:
                account = Account(
                    primary_smtp_address=email,
                    config=ews_config,
                    autodiscover=False,
                    access_type=IMPERSONATION
                )
                calendar_items = account.calendar.filter(start__gt=UTC_NOW()).order_by('-start')[:20]

                for item in calendar_items:
                    uid = item.id
                    if (
                        uid and uid not in seen_ids and
                        item.datetime_created and item.datetime_created > service_start_time and
                        item.location and magic_word.lower() in item.location.lower() and
                        item.organizer and item.organizer.email_address.lower() == account.primary_smtp_address.lower()
                    ):
                        seen_ids.add(uid)
                        logging.info(f"Match: {item.subject} | {item.start} | {item.location}")
                        user_part = email.split('@')[0]
                        details = get_meeting_details(user_part)
                        if details:
                            try:
                                with open(TEMPLATE_PATH, "r", encoding="utf-8") as template_file:
                                    html_template = template_file.read()

                                html_append = html_template \
                                    .replace("{{WEB_LINK}}", details.get("WEB_LINK", "-")) \
                                    .replace("{{SIP_ADDRESS}}", details.get("SIP_ADDRESS", "-")) \
                                    .replace("{{PIN}}", details.get("PIN", "-")) \
                                    .replace("{{callid}}", details.get("CALLID", "-"))

                                # Добавляем отступ и шаблон в конец существующего тела
                                original_body = item.body or HTMLBody("")
                                updated_body = HTMLBody(str(original_body) + "<br><br>" + html_append)

                                item.body = updated_body
                                item.save(send_meeting_invitations=SEND_TO_ALL_AND_SAVE_COPY)
                                logging.info("Meeting updated with additional HTML and participants notified")

                            except Exception as save_err:
                                logging.error(f"Failed to update meeting for {email}: {str(save_err)}")

            except Exception as e:
                err_text = str(e)
                if 'no mailbox associated' in err_text.lower():
                    failed_mailbox_users.add(email)
                    subscription_logger.error(f"Failed to process {email}: {err_text}")
                else:
                    logging.error(f"Failed to process {email}: {err_text}")

    except Exception as e:
        logging.error(f"Unexpected error in loop: {str(e)}")

    time.sleep(60)  # Delay before next loop iteration