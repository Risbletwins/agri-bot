#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "Wifi abar ki jinis";
const char* password = "passdemunah!";

const char* seed_sowing_system = "https://agri-bot-kwis.onrender.com/seed_sowing_system/button";
const char* humidity_measuring_system = "https://agri-bot-kwis.onrender.com/humidity_measuring_system/button";
const char* water_pump_system = "https://agri-bot-kwis.onrender.com/water_pump_system/button";
const char* soil_moisture_measuring_system = "https://agri-bot-kwis.onrender.com/soil_moisture_measuring_system/button";

const char* msg_of_seed_sowing_system;
const char* msg_of_humidity_measuring_system;
const char* msg_of_water_pump_system;
const char* msg_of_soil_moisture_measuring_system;

const char* on = "on";
const char* off = "off";

void setup() {
  Serial.begin(115200);

  
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
  Serial2.begin(9600, SERIAL_8N1, 16, 17);
}

void loop() {



  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
  
    // seed_sowing_system
    http.begin(seed_sowing_system);
    int httpCode = http.GET();
    if (httpCode == HTTP_CODE_OK) {
      String payload = http.getString();
      StaticJsonDocument<200> doc;
      DeserializationError error = deserializeJson(doc, payload);
      if (!error) {
        msg_of_seed_sowing_system = doc["msg"];
        Serial.print("msg_of_seed_sowing_system: ");
        Serial.println(msg_of_seed_sowing_system);
      } else {
        Serial.print("JSON parse error: ");
        Serial.println(error.c_str());
      }
    } else {
      Serial.printf("HTTP Error code (seed): %d\n", httpCode);
    }
    http.end();

    // humidity_measuring_system
    http.begin(humidity_measuring_system);
    httpCode = http.GET();
    if (httpCode == HTTP_CODE_OK) {
      String payload = http.getString();
      StaticJsonDocument<200> doc;
      DeserializationError error = deserializeJson(doc, payload);
      if (!error) {
        msg_of_humidity_measuring_system = doc["msg"];
        Serial.print("msg_of_humidity_measuring_system: ");
        Serial.println(msg_of_humidity_measuring_system);
      } else {
        Serial.print("JSON parse error: ");
        Serial.println(error.c_str());
      }
    } else {
      Serial.printf("HTTP Error code (humidity): %d\n", httpCode);
    }
    http.end();

    // water_pump_system
    http.begin(water_pump_system);
    httpCode = http.GET();
    if (httpCode == HTTP_CODE_OK) {
      String payload = http.getString();
      StaticJsonDocument<200> doc;
      DeserializationError error = deserializeJson(doc, payload);
      if (!error) {
        msg_of_water_pump_system = doc["msg"];
        Serial.print("msg_of_water_pump_system: ");
        Serial.println(msg_of_water_pump_system);
      } else {
        Serial.print("JSON parse error: ");
        Serial.println(error.c_str());
      }
    } else {
      Serial.printf("HTTP Error code (water): %d\n", httpCode);
    }
    http.end();

    // soil_moisture_measuring_system
    http.begin(soil_moisture_measuring_system);
    httpCode = http.GET();
    if (httpCode == HTTP_CODE_OK) {
      String payload = http.getString();
      StaticJsonDocument<200> doc;
      DeserializationError error = deserializeJson(doc, payload);
      if (!error) {
        msg_of_soil_moisture_measuring_system = doc["msg"];
        Serial.print("msg_of_soil_moisture_measuring_system: ");
        Serial.println(msg_of_soil_moisture_measuring_system);
      } else {
        Serial.print("JSON parse error: ");
        Serial.println(error.c_str());
      }
    } else {
      Serial.printf("HTTP Error code (soil moisture): %d\n", httpCode);
    }
    http.end();
    Serial.println(msg_of_soil_moisture_measuring_system);
    Serial.println(on);

    if (strcmp(msg_of_soil_moisture_measuring_system, on) == 0) {
    Serial.println("meaw");
    Serial2.println("on");
}else{
      Serial.println("meawww");
    Serial2.println("off");
}
   if(strcmp(msg_of_seed_sowing_system, on) == 0) {
    Serial.println("meaw");
    Serial2.println("on1");
}else{
    Serial.println("meawww");
    Serial2.println("off1");
}


  } else {
    Serial.println("WiFi disconnected!");
  }


  
  
}
