import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

DATABASE_URL = os.getenv('DATABASE_URL')

MQTT_HOST = os.getenv('MQTT_HOST')
MQTT_PORT = int(os.getenv('MQTT_PORT', '8883'))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')

MQTT_RESULT_TOPIC = os.getenv('MQTT_RESULT_TOPIC', 'indoor/esp/+/result')
MQTT_COMMAND_TOPIC_PREFIX = os.getenv('MQTT_COMMAND_TOPIC_PREFIX', 'indoor/esp')

MODEL_PATH = os.getenv(
    'MODEL_PATH',
    str(BASE_DIR / 'backend' / 'artifacts' / 'location_model.joblib')
)

FINGERPRINT_PATH = os.getenv(
    'FINGERPRINT_PATH',
    str(BASE_DIR / 'backend' / 'artifacts' / 'fingerprint_reference.csv')
)

REFERENCE_FINGERPRINT_PATH = os.getenv(
    'REFERENCE_FINGERPRINT_PATH',
    str(BASE_DIR / 'backend' / 'artifacts' / 'reference_fingerprints.json')
)

LOW_CONFIDENCE_THRESHOLD = float(os.getenv('LOW_CONFIDENCE_THRESHOLD', '0.60'))
MIN_COMMON_MACS = int(os.getenv('MIN_COMMON_MACS', '1'))
