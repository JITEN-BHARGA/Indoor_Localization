import json
import ssl
import threading
import os

from dotenv import load_dotenv
import paho.mqtt.client as mqtt

from backend.db import (
    save_raw_scan,
    save_prediction,
    complete_scan_request,
)

# ✅ correct predictor import
from backend.hybrid_predictor import hybrid_predict

load_dotenv()

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

MQTT_RESULT_TOPIC = os.getenv("MQTT_RESULT_TOPIC")
MQTT_COMMAND_TOPIC_PREFIX = os.getenv("MQTT_COMMAND_TOPIC_PREFIX")

mqtt_client = None


# ----------------------------
# MQTT READY CHECK
# ----------------------------
def is_mqtt_ready():
    return mqtt_client is not None and mqtt_client.is_connected()


# ----------------------------
# ON CONNECT
# ----------------------------
def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected rc={rc}")
    client.subscribe(MQTT_RESULT_TOPIC)
    print(f"[MQTT] Subscribed to {MQTT_RESULT_TOPIC}")


# ----------------------------
# ON MESSAGE
# ----------------------------
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print("[MQTT] Message received:", payload)

        request_id = payload.get("request_id")
        device_id = payload.get("device_id")
        object_id = payload.get("object_id")

        if not request_id or not device_id:
            print("[MQTT] Invalid payload")
            return

        # ✅ FIXED: correct parameters
        save_raw_scan(request_id, object_id, device_id, payload)

        # ✅ correct prediction function
        result = hybrid_predict(payload)

        # ✅ FIXED: correct call format
        save_prediction(result, request_id=request_id, device_id=device_id)

        # Mark complete
        complete_scan_request(request_id)

        print("[MQTT] Processed successfully")

    except Exception as e:
        print("[MQTT] Error:", e)


# ----------------------------
# START MQTT
# ----------------------------
def start_mqtt():
    global mqtt_client

    mqtt_client = mqtt.Client()

    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
    mqtt_client.tls_insecure_set(True)

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    print(f"[MQTT] Connecting to {MQTT_HOST}:{MQTT_PORT}")
    mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)

    mqtt_client.loop_forever()


def start_mqtt_in_background():
    thread = threading.Thread(target=start_mqtt)
    thread.daemon = True
    thread.start()


# ----------------------------
# PUBLISH COMMAND
# ----------------------------
def publish_scan_command(device_id: str, request_id: str, object_id: str):
    topic = f"{MQTT_COMMAND_TOPIC_PREFIX}/{device_id}/command"

    payload = {
        "request_id": request_id,
        "object_id": object_id,
        "command": "scan",
    }

    mqtt_client.publish(topic, json.dumps(payload))
    print(f"[MQTT] Published to {topic}")