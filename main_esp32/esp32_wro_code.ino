#include <Servo.h>
#include <Wire.h>
#include <ESP32Servo.h>
#include <LiquidCrystal_I2C.h>
#include <WiFi.h>
#include <HTTPClient.h>



#define solar_panel_servo 32 //o

#define soil_moisture_servo_big 33 //o
#define soil_moisture_servo_small 25 //o
#define soil_moisture_sensor 36 //i

#define esp32cam_x_axis 27 //o
#define esp32cam_y_axis 14 //o
 
#define seed_sow_servo 12 //o

#define voltage_sensor_solar_panel 39 //i
#define voltage_sensor_battery 34 //i

#define water_pump 13 //o
#define ldr_sensor 35 //i

#define humidity_sensor 19 //i

#define lcd_SDA 21 //o
#define lcd_SCL 22 //o


Servo solarPanelServo;
Servo soilMoistureServoBig;
Servo soilMoistureServoSmall;
Servo esp32CamXServo;
Servo esp32camYServo;
Servo seedSowServo;

LiquidCrystal_I2C lcd (0x27, 20, 4);

int light_state = 0;
int fertilizer_state = 0;
int seed_sow_state = 0;


const char* ssid = "Proteek Mesh";
const char* password = "passwordnaisorry";
const char* serverName = "https://agri-bot-kwis.onrender.com/esp32-receive/"; 

void setup() {
  Serial.begin(115200);


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

    http.begin(serverName);          
    int httpResponseCode = http.GET(); 

    if (httpResponseCode > 0) {
      Serial.print("Response code: ");
      Serial.println(httpResponseCode);

      String response = "";
      response = http.getString(); 
      Serial.println("Server response:");
      Serial.println(response); 
    } else {
      Serial.print("Error code: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  }


















}