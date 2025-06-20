import logging
import configparser
import os
import requests
from datetime import datetime
from xml.etree import ElementTree
import warnings

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'settings.ini')
USERS_PATH = os.path.join(BASE_DIR, 'config', 'users.txt')
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'cmssync.log')

# Load config
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

cms_url = config['CMS API']['base_cms_url']
apiuser = config['CMS API']['apiuser']
apipwd = config['CMS API']['apipwd']
mail_domain = config['EWS']['mail_domain']
log_level = config['Logging']['log_level'].upper()

# Logging
logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, log_level),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
warnings.filterwarnings("ignore")

def get_cms_users():
    users = []
    offset = 0
    limit = 20
    headers = {'Accept': 'application/xml'}

    while True:
        url = f"{cms_url}users?offset={offset}&limit={limit}"
        resp = requests.get(url, auth=(apiuser, apipwd), verify=False, headers=headers)
        if resp.status_code != 200:
            logging.error(f"Failed to fetch users from CMS: {resp.status_code} {resp.text}")
            break

        root = ElementTree.fromstring(resp.text)
        for user in root.findall(".//user"):
            jid_elem = user.find('userJid')
            if jid_elem is not None and jid_elem.text:
                jid = jid_elem.text
                username = jid.split('@')[0] + mail_domain
                users.append(username)
            else:
                logging.warning("Skipping user without valid <userJid>")

        total = int(root.attrib.get('total', len(users)))
        if len(users) >= total:
            break
        offset += limit

    return users

def save_users(users):
    os.makedirs(os.path.dirname(USERS_PATH), exist_ok=True)
    with open(USERS_PATH, 'w') as f:
        f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n')
        for u in users:
            f.write(u + '\n')

if __name__ == '__main__':
    logging.info("Starting CMS user sync...")
    users = get_cms_users()
    if users:
        save_users(users)
        logging.info(f"Saved {len(users)} users to users.txt")
    else:
        logging.warning("No users retrieved.")
