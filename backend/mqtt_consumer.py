import json
import ssl
import threading
from collections import defaultdict
import paho.mqtt.client as mqtt

from backend.config import (
    MQTT_HOST,
    MQTT_PORT,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    MQTT_RESULT_TOPIC,
    MQTT_COMMAND_TOPIC_PREFIX,
)
from backend.hybrid_predictor import hybrid_predict
from backend.db import (
    save_raw_scan,
    save_prediction,
    mark_device_response_received,
    get_scan_request_status,
    get_raw_scans_for_request,
    complete_scan_request,
    touch_esp_device,
)

mqtt_client = None


def is_mqtt_ready():
    global mqtt_client
    return mqtt_client is not None and mqtt_client.is_connected()


def merge_scan_payloads(scan_payloads: list[dict]) -> dict:
    if not scan_payloads:
        raise ValueError("No scan payloads to merge")

    object_id = scan_payloads[0]["object_id"]
    rssi_map = defaultdict(list)

    for payload in scan_payloads:
        for item in payload.get("scan_data", []):
            mac = item["mac_address"].strip().upper()
            rssi_map[mac].append(float(item["rssi"]))

    merged_scan_data = []
    for mac, values in rssi_map.items():
        avg_rssi = sum(values) / len(values)
        merged_scan_data.append({
            "mac_address": mac,
            "rssi": int(round(avg_rssi))
        })

    return {
        "object_id": object_id,
        "device_id": "merged",
        "scan_data": merged_scan_data,
    }


def try_finalize_request(request_id: str):
    status = get_scan_request_status(request_id)
    if not status:
        return

    if status["expected_device_count"] == 0:
        return

    if status["received_device_count"] < status["expected_device_count"]:
        return

    existing_result = get_raw_scans_for_request(request_id)
    if not existing_result:
        return

    merged_payload = merge_scan_payloads(existing_result)
    result = hybrid_predict(merged_payload)
    save_prediction(result, request_id=request_id)
    complete_scan_request(request_id)


def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"[MQTT] Connected rc={reason_code}")
    client.subscribe(MQTT_RESULT_TOPIC)
    print(f"[MQTT] Subscribed to {MQTT_RESULT_TOPIC}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        print("[MQTT] Message received:", payload)

        request_id = payload.get("request_id")
        object_id = payload["object_id"]
        device_id = payload.get("device_id", "unknown")

        save_raw_scan(
            request_id=request_id,
            object_id=object_id,
            device_id=device_id,
            payload=payload,
        )

        touch_esp_device(device_id)

        if request_id:
            mark_device_response_received(request_id, device_id)
            try_finalize_request(request_id)
        else:
            result = hybrid_predict(payload)
            save_prediction(result)

        print("[MQTT] Processed payload successfully")

    except Exception as e:
        print("[MQTT] Error:", e)


def start_mqtt_consumer():
    global mqtt_client

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.tls_insecure_set(True)

        client.on_connect = on_connect
        client.on_message = on_message

        print(f"[MQTT] Connecting to {MQTT_HOST}:{MQTT_PORT}")
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_start()

        mqtt_client = client
        print("[MQTT] Client started successfully")

    except Exception as e:
        mqtt_client = None
        print(f"[MQTT] Startup failed: {e}")


def publish_scan_command(device_id: str, request_id: str, object_id: str):
    global mqtt_client

    if not is_mqtt_ready():
        raise RuntimeError("MQTT client is not started or not connected")

    topic = f"{MQTT_COMMAND_TOPIC_PREFIX}/{device_id}/command"
    payload = {
        "request_id": request_id,
        "object_id": object_id,
        "command": "scan",
    }

    info = mqtt_client.publish(topic, json.dumps(payload), qos=1)
    info.wait_for_publish()

    print(f"[MQTT] Published scan command to {topic}: {payload}")
    print(f"[MQTT] publish mid={info.mid}, rc={info.rc}, is_published={info.is_published()}")

    if info.rc != mqtt.MQTT_ERR_SUCCESS:
        raise RuntimeError(f"MQTT publish failed with rc={info.rc}")


def start_mqtt_in_background():
    thread = threading.Thread(target=start_mqtt_consumer, daemon=True)
    thread.start()