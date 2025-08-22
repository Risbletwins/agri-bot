#include <Servo.h>
#include <Wire.h>
#include <ESP32Servo.h>
#include <LiquidCrystal_I2C.h>
#include <WiFi.h>
#include <HTTPClient.h>



#define solar_panel_servo 33 //o

#define soil_moisture_servo_big 25 //o
#define soil_moisture_servo_small 26 //o

#define soil_moisture_sensor 36 //i

#define esp32cam_x_axis 27 //o
#define esp32cam_y_axis 14 //o
 
#define seed_sow_servo 13 //o

#define voltage_sensor_solar_panel 39//i
#define voltage_sensor_battery 34 //i

#define water_pump 2 //o
#define ldr_sensor 35 //i
#define light 0//o

#define humidity_sensor 32 //i

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
int water_pump_state = 0;


const char* ssid = "Proteek Mesh";
const char* password = "passwordnaisorry";
const char* serverName = "https://agri-bot-kwis.onrender.com/esp32-receive/"; 

//infinte defining ends here 

void setup() {
  
  Serial.begin(115200);


  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");

  solarPanelServo.attach(solar_panel_servo);
  soilMoistureServoBig.attach(soil_moisture_servo_big);
  soilMoistureServoSmall.attach(soil_moisture_servo_small);
  esp32CamXServo.attach(esp32cam_x_axis);
  esp32camYServo.attach(esp32cam_y_axis);
  seedSowServo.attach(seed_sow_servo);

  solarPanelServo.write(0);
  soilMoistureServoBig.write(0);
  soilMoistureServoSmall.write(0);
  esp32CamXServo.write(0);
  esp32camYServo.write(0);
  seedSowServo.write(0);

  pinMode(voltage_sensor_solar_panel, INPUT);
  pinMode(voltage_sensor_battery, INPUT);
  pinMode(humidity_sensor, INPUT);
  pinMode(ldr_sensor, INPUT);
  pinMode(soil_moisture_sensor,INPUT);

  pinMode(water_pump, OUTPUT);
  pinMode(light, OUTPUT);

  Wire.begin(lcd_SDA, lcd_SCL); 
  lcd.init();
  lcd.backlight();

}

void loop() {

  //getting the responses from web

  String response = "";
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    http.begin(serverName);          
    int httpResponseCode = http.GET(); 

    if (httpResponseCode > 0) {
      Serial.print("Response code: ");
      Serial.println(httpResponseCode);

      
      response = http.getString(); 
      Serial.println("Server response:");
      Serial.println(response); 
    } else {
      Serial.print("Error code: ");
      Serial.println(httpResponseCode);
    }

    http.end();

    //this code rejwan bhai should understand

    if (response == "light_on"){
      light_state = 1;
    }
    if (response == "light_off"){
      light_state = 0;
    }
    if (response == "fertilizer_on"){
      fertilizer_state = 1;
    }
    if (response == "fertilizer_off"){
      fertilizer_state = 0;
    }
    if (response == "water_pump_on"){
      water_pump_state = 1;
    }
    if (response == "water_pump_off"){
      water_pump_state = 0;
    }
    if (response == "seed_sow_on"){
      seed_sow_state = 1;
    }
    if (response == "seed_sow_off"){
      seed_sow_state = 0;
    }

    if(light_state == 0){

      digitalWrite(light,LOW);
    }
    if(light_state == 1){

      digitalWrite(light,HIGH);
    }
    if(water_pump_state == 0){

      digitalWrite(water_pump,LOW);
    }
    if(water_pump_state == 1){

      digitalWrite(water_pump,HIGH);
    }
    if(fertilizer_state == 0){
      
    }
    if(fertilizer_state == 1){
      
    }
    if(seed_sow_state == 0){
      
    }
    if(seed_sow_state == 1){
      
    }
      

    
  }


















}