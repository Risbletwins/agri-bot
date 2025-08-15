#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "TECNO SPARK Go 1";
const char* password = "123456678";

const char* seed_sowing_system = "https://agri-bot-kwis.onrender.com/seed_sowing_system/button";
const char* humidity_measuring_system = "https://agri-bot-kwis.onrender.com/humidity_measuring_system/button";
const char* water_pump_system = "https://agri-bot-kwis.onrender.com/water_pump_system/button";
const char* soil_moisture_measuring_system = "https://agri-bot-kwis.onrender.com/soil_moisture_measuring_system/button";

const char* msg_of_seed_sowing_system;
const char* msg_of_humidity_measuring_system;
const char* msg_of_water_pump_system;
const char* msg_of_soil_moisture_measuring_system;

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
    Serial.prinln("meaw");
    Serial.println(msg_of_soil_moisture_measuring_system);
    Serial.println(msg_of_seed_sowing_system);
    

    if (strcmp(msg_of_soil_moisture_measuring_system, "soil_mos_on") == 0) {
    Serial.println("soil_mos_on");
    Serial2.println("soil_mos_on");
}else{
    Serial.println("soil_mos_off");
    Serial2.println("soil_mos_off");
}
   if(strcmp(msg_of_seed_sowing_system, "seed_sowing_on") == 0) {
    Serial.println("seed_sowing_on");
    Serial2.println("seed_sowing_on");
}else{
    Serial.println("seed_sowing_off");
    Serial2.println("seed_sowing_off");
}


  } else {
    Serial.println("WiFi disconnected!");
  }


  
  
}
