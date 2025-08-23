#include <ESP32Servo.h> // Use only ESP32Servo for ESP32
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <WiFi.h>
#include <HTTPClient.h>

#define solar_panel_servo 26
#define soil_moisture_servo_big 33
#define soil_moisture_servo_small 25
#define esp32cam_x_axis 27
#define esp32cam_y_axis 14
#define seed_sow_servo 13

#define soil_moisture_sensor 35
#define voltage_sensor_solar_panel 39
#define voltage_sensor_battery 34
#define water_pump 2
#define ldr_sensor 36
#define light 0
#define humidity_sensor 32
#define lcd_SDA 21
#define lcd_SCL 22

Servo solarPanelServo;
Servo soilMoistureServoBig;
Servo soilMoistureServoSmall;
Servo esp32CamXServo;
Servo esp32camYServo;
Servo seedSowServo;

LiquidCrystal_I2C lcd(0x27, 20, 4);

int light_state = 0;
int fertilizer_state = 0;
int seed_sow_state = 0;
int water_pump_state = 0;
int soil_moisture_state = 0;

const char* ssid = "Proteek Mesh";
const char* password = "passwordnaisorry";
const char* serverName = "https://agri-bot-kwis.onrender.com/esp32-receive/";

unsigned long previousMillis = 0;
const long interval = 1000;

void setup() {
  Serial.begin(115200);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");


  ESP32PWM::allocateTimer(0); 
  ESP32PWM::allocateTimer(1);
  solarPanelServo.setPeriodHertz(50); 
  soilMoistureServoBig.setPeriodHertz(50);
  soilMoistureServoSmall.setPeriodHertz(50);
  esp32CamXServo.setPeriodHertz(50);
  esp32camYServo.setPeriodHertz(50);
  seedSowServo.setPeriodHertz(50);

  if (!solarPanelServo.attach(solar_panel_servo, 500, 2500)) {
    Serial.println("Failed to attach solarPanelServo... what a pain..");
  }
  if (!soilMoistureServoBig.attach(soil_moisture_servo_big, 500, 2500)) {
    Serial.println("Failed to attach soilMoistureServoBig... what a pain..");
  }
  if (!soilMoistureServoSmall.attach(soil_moisture_servo_small, 500, 2500)) {
    Serial.println("Failed to attach soilMoistureServoSmall... what a pain..");
  }
  if (!esp32CamXServo.attach(esp32cam_x_axis, 500, 2500)) {
    Serial.println("Failed to attach esp32CamXServo... what a pain..");
  }
  if (!esp32camYServo.attach(esp32cam_y_axis, 500, 2500)) {
    Serial.println("Failed to attach esp32camYServo... what a pain..");
  }
  if (!seedSowServo.attach(seed_sow_servo, 500, 2500)) {
    Serial.println("Failed to attach seedSowServo... what a pain..");
  }

  // Set initial servo positions
  solarPanelServo.write(0);
  soilMoistureServoBig.write(0);
  soilMoistureServoSmall.write(0);
  esp32CamXServo.write(0);
  esp32camYServo.write(0);
  seedSowServo.write(90);

  // Initialize pins
  pinMode(voltage_sensor_solar_panel, INPUT);
  pinMode(voltage_sensor_battery, INPUT);
  pinMode(humidity_sensor, INPUT);
  pinMode(ldr_sensor, INPUT);
  pinMode(soil_moisture_sensor, INPUT);
  pinMode(water_pump, OUTPUT);
  pinMode(light, OUTPUT);

  // Initialize LCD
  Wire.begin(lcd_SDA, lcd_SCL);
  lcd.init();
  lcd.backlight();
}

String response = "";
String previous_response = response;

void loop() {
  unsigned long currentMillis = millis();

  // Check WiFi and send HTTP request periodically
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;

    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(serverName);
      int httpResponseCode = http.GET();

      if (httpResponseCode > 0) {
        Serial.print("Response code: ");
        Serial.println(httpResponseCode);
        previous_response = response;
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

  // Process server response
  if (response == "light_on") {
    light_state = HIGH;
  }if (response == "light_off") {
    light_state = LOW;
  }if (response == "fertilizer_on") {
    fertilizer_state = 1;
  }if (response == "fertilizer_off") {
    fertilizer_state = 0;
  }if (response == "water_pump_on") {
    water_pump_state = HIGH;
  }if (response == "water_pump_off") {
    water_pump_state = LOW;
  }if (response == "seed_sow_on") {
    seed_sow_state = 1;
  }if (response == "seed_sow_off") {
    seed_sow_state = 0;
  }if (response == "start_measuring_soil_moisture"){
    soil_moisture_state = 1;
  }
  if (response == "stop_measuring_soil_moisture"){
    soil_moisture_state = 0;
  }
  


  digitalWrite(light, light_state);
  digitalWrite(water_pump, water_pump_state);

  if (fertilizer_state == 1 || seed_sow_state == 1) {
    if (seedSowServo.read() != 90) { // Only move if not already at position
      seedSowServo.write(90);
      delay(500);
    }
    if (seedSowServo.read() != 180) { // Only move if not already at position
      seedSowServo.write(180);
      delay(500);
    }
  } else {

  }
  if(soil_moisture_state == 1){
    soilMoistureServoBig.write(40);
    delay(1000);
    soilMoistureServoSmall.write(140);
    delay(1000);
    int soil_moisture_read = analogRead(soil_moisture_sensor);
    Serial.print("Soil Moisture: ");
    Serial.println(soil_moisture_read);
    lcd.setCursor(0,0);
    lcd.print(soil_moisture_read);
    lcd.setCursor(1,0);
    lcd.print("ShahratbhaiGJ");

  }else{
    soilMoistureServoBig.write(90);
    delay(1000);
    soilMoistureServoSmall.write(90);
    delay(1000);
  }
}