import json
import ssl
import threading
import paho.mqtt.client as mqtt

from backend.config import MQTT_HOST, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, MQTT_TOPIC
from backend.hybrid_predictor import hybrid_predict
from backend.db import save_raw_scan, save_prediction


def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[MQTT] Connected rc={rc}")
    client.subscribe(MQTT_TOPIC)
    print(f"[MQTT] Subscribed to {MQTT_TOPIC}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        print("[MQTT] Message received:", payload)

        save_raw_scan(
            object_id=payload["object_id"],
            device_id=payload.get("device_id", "unknown"),
            payload=payload,
        )

        result = hybrid_predict(payload)
        save_prediction(result)

        print("[MQTT] Hybrid Result:", result)

    except Exception as e:
        print("[MQTT] Error:", e)


def start_mqtt_consumer():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()


def start_mqtt_in_background():
    thread = threading.Thread(target=start_mqtt_consumer, daemon=True)
    thread.start()