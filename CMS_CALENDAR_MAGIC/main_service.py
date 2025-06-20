import subprocess
import threading
import time
import configparser
import logging
import os
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'settings.ini')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
LOG_FILE = os.path.join(LOGS_DIR, 'subscriptions.log')
CMS_SYNC_SCRIPT = os.path.join(BASE_DIR, 'cms_sync.py')
CALENDAR_CON_SCRIPT = os.path.join(BASE_DIR, 'calendar_con.py')

# Создаём папку logs, если её нет
os.makedirs(LOGS_DIR, exist_ok=True)

# Load config
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

sync_time_str = config['CMS API']['users_synctime']  # e.g., "00:00"
log_level = config['Logging']['log_level'].upper()

# Logging
logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, log_level),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_cms_sync():
    while True:
        now = datetime.now().strftime('%H:%M')
        if now == sync_time_str:
            logging.info("Scheduled CMS user sync starting...")
            subprocess.run(['python', CMS_SYNC_SCRIPT])
            time.sleep(60)  # Prevent re-trigger within same minute
        time.sleep(10)

def run_calendar_monitor():
    logging.info("Starting calendar monitor loop...")
    subprocess.run(['python', CALENDAR_CON_SCRIPT])

if __name__ == '__main__':
    # Initial CMS sync
    logging.info("Running initial CMS sync...")
    subprocess.run(['python', CMS_SYNC_SCRIPT])

    # Background daily sync
    threading.Thread(target=run_cms_sync, daemon=True).start()

    # Start calendar monitoring (blocking)
    run_calendar_monitor()