#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "Proteek Mesh";
const char* password = "passwordnaisorry";
const char* serverName = "https://localhost:5000/api"; // Your Flask endpoint

void setup() {
  Serial.begin(115200);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");

  // Send POST request
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");  // Send as JSON

    String jsonData = "{\"name\":\"Nuslan\",\"age\":17}";

    int httpResponseCode = http.POST(jsonData);

    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);

    String payload = http.getString();
    Serial.println("Server response:");
    Serial.println(payload);

    http.end();
  }
}

void loop() {
  // Nothing here
}
