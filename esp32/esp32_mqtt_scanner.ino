#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WIFI CONFIG
const char* WIFI_SSID = "Galaxy A04s E5D9";
const char* WIFI_PASSWORD = "jiten@2005";

// HIVEMQ CLOUD CONFIG
const char* MQTT_HOST = "71d42413ef0d4e608f50a83715ac6ba7.s1.eu.hivemq.cloud";
const int MQTT_PORT = 8883;
const char* MQTT_USERNAME = "jb_8115";
const char* MQTT_PASSWORD = "Jiten@333";

// ===============================
// Unique ESP device identity
// Must match esp_devices.device_id in DB
// ===============================
const char* DEVICE_ID = "esp32_01";

// Topics
String commandTopic;
String resultTopic;

// Secure client
WiFiClientSecure secureClient;
PubSubClient mqttClient(secureClient);

// Last command context
String currentRequestId = "";
String currentObjectId = "";

// ===============================
// Connect WiFi
// ===============================
void connectWiFi() {
  Serial.println("Connecting to WiFi...");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

// ===============================
// MQTT callback
// ===============================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.println("MQTT message received");

  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("Topic: ");
  Serial.println(topic);
  Serial.print("Payload: ");
  Serial.println(message);

  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, message);

  if (error) {
    Serial.print("JSON parse failed: ");
    Serial.println(error.c_str());
    return;
  }

  const char* command = doc["command"];
  const char* request_id = doc["request_id"];
  const char* object_id = doc["object_id"];

  if (!command || !request_id || !object_id) {
    Serial.println("Invalid command payload");
    return;
  }

  if (String(command) == "scan") {
    currentRequestId = String(request_id);
    currentObjectId = String(object_id);

    Serial.println("Scan command received");
    Serial.print("Request ID: ");
    Serial.println(currentRequestId);
    Serial.print("Object ID: ");
    Serial.println(currentObjectId);

    performAndPublishScan();
  }
}

// ===============================
// Connect MQTT
// ===============================
void connectMQTT() {
  while (!mqttClient.connected()) {
    Serial.println("Connecting to MQTT...");

    String clientId = "ESP32-" + String(DEVICE_ID) + "-" + String(random(1000, 9999));

    if (mqttClient.connect(clientId.c_str(), MQTT_USERNAME, MQTT_PASSWORD)) {
      Serial.println("MQTT connected");

      if (mqttClient.subscribe(commandTopic.c_str())) {
        Serial.print("Subscribed to: ");
        Serial.println(commandTopic);
      } else {
        Serial.println("MQTT subscribe failed");
      }

    } else {
      Serial.print("MQTT connect failed, rc=");
      Serial.println(mqttClient.state());
      delay(2000);
    }
  }
}

// ===============================
// Perform WiFi scan and publish
// ===============================
void performAndPublishScan() {
  Serial.println("Starting WiFi scan...");

  int networkCount = WiFi.scanNetworks(false, true);

  if (networkCount < 0) {
    Serial.println("WiFi scan failed");
    return;
  }

  StaticJsonDocument<8192> doc;
  doc["request_id"] = currentRequestId;
  doc["object_id"] = currentObjectId;
  doc["device_id"] = DEVICE_ID;

  JsonArray scanData = doc.createNestedArray("scan_data");

  for (int i = 0; i < networkCount; i++) {
    JsonObject item = scanData.createNestedObject();
    item["mac_address"] = WiFi.BSSIDstr(i);
    item["rssi"] = WiFi.RSSI(i);
    item["ssid"] = WiFi.SSID(i);
    item["channel"] = WiFi.channel(i);
  }

  char buffer[8192];
  size_t payloadSize = serializeJson(doc, buffer);

  Serial.println("Publishing scan result...");
  Serial.print("Topic: ");
  Serial.println(resultTopic);
  Serial.print("Payload size: ");
  Serial.println(payloadSize);

  bool ok = mqttClient.publish(resultTopic.c_str(), buffer, payloadSize);

  if (ok) {
    Serial.println("Scan result published successfully");
  } else {
    Serial.println("Failed to publish scan result");
  }

  WiFi.scanDelete();
}

// ===============================
// Setup
// ===============================
void setup() {
  Serial.begin(115200);
  delay(1000);

  randomSeed(micros());

  commandTopic = "indoor/esp/" + String(DEVICE_ID) + "/command";
  resultTopic = "indoor/esp/" + String(DEVICE_ID) + "/result";

  connectWiFi();

  secureClient.setInsecure();

  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  mqttClient.setBufferSize(16384);

  connectMQTT();
}

// ===============================
// Loop
// ===============================
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  if (!mqttClient.connected()) {
    connectMQTT();
  }

  mqttClient.loop();
}