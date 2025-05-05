#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

#define DHTPIN 4            // DHT22 data pin
#define DHTTYPE DHT11
#define RELAY_PIN 5  

const char* ssid = "Airtel_BenDover";
const char* pass = "gtbtct2001";
const char* server = "http://172.20.10.4:8000/api/data"; // Replace with your IP or domain
//const char* server = "http://192.168.1.6:8000/api/data"; // Replace with your IP or domain
DHT dht(DHTPIN, DHTTYPE);

// User-controlled variables
bool masterSwitch = true;
float tempCutoff = 75.0;      // Default °F
float humidityCutoff = 20.0;  // Default %

void setup() {
  Serial.begin(115200);

  dht.begin();
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH); // Start with pump OFF

  WiFi.begin(ssid, pass);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected.");
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature(); // Celsius
  float f = t * 9 / 5 + 32;        // Fahrenheit

  if (!isnan(h) && !isnan(f)) {
    Serial.printf("Temp: %.2f°F, Humidity: %.2f%%\n", f, h);

    // Decide pump status
    bool shouldTurnOn = (masterSwitch && (f < tempCutoff || h < humidityCutoff));
    digitalWrite(RELAY_PIN, shouldTurnOn ? LOW : HIGH); // Active LOW relay
    Serial.println(shouldTurnOn ? "Pump ON" : "Pump OFF");

    // Prepare JSON
    StaticJsonDocument<200> jsonDoc;
    jsonDoc["device_id"] = "esp32-001";
    jsonDoc["temperature"] = f;
    jsonDoc["humidity"] = h;
    jsonDoc["timestamp"] = ""; // Let server set timestamp if desired

    String jsonData;
    serializeJson(jsonDoc, jsonData);

    // Send HTTP POST
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(server);
      http.addHeader("Content-Type", "application/json");

      int httpResponseCode = http.POST(jsonData);
      if (httpResponseCode > 0) {
        Serial.printf("Data sent, response: %d\n", httpResponseCode);
      } else {
        Serial.printf("Failed to send data: %s\n", http.errorToString(httpResponseCode).c_str());
      }
      http.end();
    } else {
      Serial.println("WiFi not connected");
    }
  } else {
    Serial.println("Failed to read from DHT sensor");
  }

  delay(5000); // Every 5 seconds
}
