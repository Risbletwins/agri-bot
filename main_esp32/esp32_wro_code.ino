#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "Proteek Mesh";
const char* password = "passwordnaisorry";
const char* serverName = "https://agri-bot-kwis.onrender.com/esp32-receive/"; // Flask endpoint or any API

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
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    http.begin(serverName);          // Specify URL
    int httpResponseCode = http.GET(); // Send GET request

    if (httpResponseCode > 0) {
      Serial.print("Response code: ");
      Serial.println(httpResponseCode);

      String response = ""; // Create string to store response
      response = http.getString(); // Store response in string
      Serial.println("Server response:");
      Serial.println(response); // Print stored response
    } else {
      Serial.print("Error code: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  }
  // Optional: Add delay to prevent flooding the server with requests
  delay(5000); // Wait 5 seconds before next request
}