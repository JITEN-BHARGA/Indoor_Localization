#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>

// WIFI CONFIG
const char* WIFI_SSID = "Galaxy A04s E5D9";
const char* WIFI_PASSWORD = "jiten@2005";

// HIVEMQ CLOUD CONFIG
const char* MQTT_HOST = "71d42413ef0d4e608f50a83715ac6ba7.s1.eu.hivemq.cloud";
const int MQTT_PORT = 8883;
const char* MQTT_USERNAME = "jb_8115";
const char* MQTT_PASSWORD = "Jiten@333";
const char* MQTT_TOPIC = "esp32/rssi";

// DEVICE INFO
const char* OBJECT_ID = "bag_01";
const char* DEVICE_ID = "esp32_01";

WiFiClientSecure secureClient;
PubSubClient client(secureClient);

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.print("Connecting WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi Connected!");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());
}

void connectMQTT() {
  secureClient.setInsecure();
  client.setServer(MQTT_HOST, MQTT_PORT);
  client.setBufferSize(2048);   // IMPORTANT

  while (!client.connected()) {
    Serial.print("Connecting MQTT to ");
    Serial.print(MQTT_HOST);
    Serial.print(":");
    Serial.println(MQTT_PORT);

    bool ok = client.connect(DEVICE_ID, MQTT_USERNAME, MQTT_PASSWORD);

    if (ok) {
      Serial.println("MQTT Connected!");
      Serial.print("MQTT Buffer Size: ");
      Serial.println(client.getBufferSize());
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying...");
      delay(2000);
    }
  }
}

String buildPayload() {
  int n = WiFi.scanNetworks(false, true);

  // only send top 5 strongest networks
  int limit = n;
  if (limit > 5) limit = 5;

  String payload = "{";
  payload += "\"object_id\":\"" + String(OBJECT_ID) + "\",";
  payload += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  payload += "\"scan_data\":[";

  for (int i = 0; i < limit; i++) {
    payload += "{";
    payload += "\"mac_address\":\"" + WiFi.BSSIDstr(i) + "\",";
    payload += "\"rssi\":" + String(WiFi.RSSI(i));
    payload += "}";

    if (i != limit - 1) payload += ",";
  }

  payload += "]}";
  return payload;
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  connectWiFi();
  connectMQTT();
}

void loop() {
  connectWiFi();

  if (!client.connected()) {
    connectMQTT();
  }

  client.loop();

  String payload = buildPayload();

  Serial.print("Payload length: ");
  Serial.println(payload.length());
  Serial.println(payload);

  bool sent = client.publish(MQTT_TOPIC, payload.c_str());

  Serial.print("Publish status: ");
  Serial.println(sent ? "SUCCESS" : "FAILED");

  delay(5000);
}