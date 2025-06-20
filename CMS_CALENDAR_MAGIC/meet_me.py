import requests
import configparser
import logging
import os
from xml.etree import ElementTree

# Пути к файлам (подкорректируйте при необходимости)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'settings.ini')
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'meetings.log')

# Загрузка настроек
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

cms_url = config['CMS API']['base_cms_url']
apiuser = config['CMS API']['apiuser']
apipwd = config['CMS API']['apipwd']
personal_room = config['CMS API']['personal_room']
wb_url = config['CMS API']['wb_url']
sipdomain = config['CMS API']['sipdomain']
log_level = config['Logging'].get('log_level', 'INFO').upper()

logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_meeting_details(user_id):
    try:
        # Получаем coSpaceID по user_id
        filter_str = f"{user_id}.{personal_room}"
        query = f"{cms_url}coSpaces?filter={filter_str}"
        headers = {'Accept': 'application/xml'}
        resp = requests.get(query, auth=(apiuser, apipwd), verify=False, headers=headers)
        if resp.status_code != 200:
            logging.warning(f"Failed to get coSpace for {user_id}: {resp.status_code}")
            return None

        root = ElementTree.fromstring(resp.text)
        coSpace = root.find(".//coSpace")
        if coSpace is None or 'id' not in coSpace.attrib:
            logging.info(f"No coSpace found for {user_id} (filter: {filter_str})")
            return None

        coSpaceID = coSpace.attrib['id']

        # Получаем детали комнаты (uri, callId, passcode, secret)
        details_url = f"{cms_url}coSpaces/{coSpaceID}/"
        resp = requests.get(details_url, auth=(apiuser, apipwd), verify=False, headers=headers)
        if resp.status_code != 200:
            logging.warning(f"Failed to get meeting details for {user_id}: {resp.status_code}")
            return None

        logging.debug(f"DETAIL XML: {resp.text}")

        # Разбор XML с учетом возможного namespace
        def find_in_xml(root_elem, tag):
            # Пытаемся с и без namespace
            res = root_elem.find(f".//{tag}")
            if res is not None:
                return res.text
            for child in root_elem.iter():
                if child.tag.endswith(tag):
                    return child.text
            return None

        detail_root = ElementTree.fromstring(resp.text)
        uri      = find_in_xml(detail_root, "uri")
        callId   = find_in_xml(detail_root, "callId")
        passcode = find_in_xml(detail_root, "passcode")
        secret   = find_in_xml(detail_root, "secret")

        # Если passcode отсутствует — подставить "нет"
        if passcode is None or passcode == "":
            passcode = "нет"

        # Требуем только uri, callId и secret (passcode теперь необязателен)
        if not all([uri, callId, secret]):
            logging.warning(f"Incomplete coSpace details for {user_id}! parsed: {uri}, {callId}, {passcode}, {secret}")
            return None
        
       
        WEB_LINK = f"{wb_url}meeting/{callId}?secret={secret}"
        SIP_ADDRESS = f"{uri}{sipdomain}"
        CALLID = callId
        PIN = passcode

        logging.info(f"Meeting details for {user_id}: WEB_LINK={WEB_LINK}, SIP_ADDRESS={SIP_ADDRESS}, CALLID={CALLID}, PIN={PIN}")

        return {
            'WEB_LINK': WEB_LINK,
            'SIP_ADDRESS': SIP_ADDRESS,
            'CALLID': CALLID,
            'PIN': PIN,
            # Дополнительно, если нужно
            'uri': uri,
            'callId': callId,
            'passcode': passcode,
            'secret': secret
        }

    except Exception as e:
        logging.error(f"Exception getting meeting details for {user_id}: {str(e)}")
        return None

# Можешь протестировать функцию так:
# if __name__ == "__main__":
#     print(get_meeting_details('vbidnyy'))