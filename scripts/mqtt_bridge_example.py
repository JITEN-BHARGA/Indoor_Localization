"""
Optional helper for local or non-Vercel use.

This script subscribes to an MQTT topic and forwards each payload to the HTTP ingest API.
It is not intended to run on Vercel.
"""

import json
import os
import paho.mqtt.client as mqtt
import requests
import dotenv
dotenv.load_dotenv()

MQTT_HOST = os.getenv('MQTT_HOST', '10.63.44.155')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'esp32/rssi')
API_URL = os.getenv('API_URL', 'http://127.0.0.1:8000/api/ingest')
API_TOKEN = os.getenv('API_TOKEN', '')

MQTT_HOST = os.getenv('MQTT_HOST', 'broker.hivemq.com')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'esp32/rssi')
API_URL = os.getenv('API_URL', 'http://127.0.0.1:8000/api/ingest')
API_TOKEN = os.getenv('API_TOKEN', '')


def on_connect(client, userdata, flags, rc, properties=None):
    print('Connected with code', rc)
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    print('Forwarding MQTT message to API...')
    headers = {'Content-Type': 'application/json'}
    if API_TOKEN:
        headers['x-api-token'] = API_TOKEN
    requests.post(API_URL, data=msg.payload, headers=headers, timeout=30)


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_forever()
