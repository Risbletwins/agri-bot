#include <ESP32Servo.h>
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

// State machine for seed sowing/fertilizer servo
enum SeedSowState { IDLE, MOVE_TO_90, WAIT_90, MOVE_TO_180, WAIT_180 };
SeedSowState seedSowCurrentState = IDLE;
unsigned long seedSowLastTransition = 0;
const long servoWaitTime = 500; // Wait time between servo movements (ms)

// State machine for soil moisture measurement
enum SoilMoistureState { INACTIVE, MOVE_BIG_TO_40, WAIT_BIG_40, MOVE_SMALL_TO_140, WAIT_SMALL_140, READ_SENSOR, MOVE_BIG_TO_90, WAIT_BIG_90, MOVE_SMALL_TO_90, WAIT_SMALL_90 };
SoilMoistureState soilMoistureCurrentState = INACTIVE;
unsigned long soilMoistureLastTransition = 0;
const long soilMoistureWaitTime = 1000; // Wait time for soil moisture servo movements (ms)

void setup() {
  Serial.begin(115200);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  unsigned long wifiStartTime = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - wifiStartTime >= 500) {
      Serial.print(".");
      wifiStartTime = millis();
    }
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

  solarPanelServo.write(0);
  soilMoistureServoBig.write(0);
  soilMoistureServoSmall.write(0);
  esp32CamXServo.write(0);
  esp32camYServo.write(0);
  seedSowServo.write(90);

  pinMode(voltage_sensor_solar_panel, INPUT);
  pinMode(voltage_sensor_battery, INPUT);
  pinMode(humidity_sensor, INPUT);
  pinMode(ldr_sensor, INPUT);
  pinMode(soil_moisture_sensor, INPUT);
  pinMode(water_pump, OUTPUT);
  pinMode(light, OUTPUT);

  Wire.begin(lcd_SDA, lcd_SCL);
  lcd.init();
  lcd.backlight();
}

String response = "";
String previous_response = response;

void loop() {
  unsigned long currentMillis = millis();

  // Handle WiFi and HTTP requests
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
  } else if (response == "light_off") {
    light_state = LOW;
  } else if (response == "fertilizer_on") {
    fertilizer_state = 1;
  } else if (response == "fertilizer_off") {
    fertilizer_state = 0;
  } else if (response == "water_pump_on") {
    water_pump_state = HIGH;
  } else if (response == "water_pump_off") {
    water_pump_state = LOW;
  } else if (response == "seed_sow_on") {
    seed_sow_state = 1;
  } else if (response == "seed_sow_off") {
    seed_sow_state = 0;
  } else if (response == "start_measuring_soil_moisture") {
    soil_moisture_state = 1;
  } else if (response == "stop_measuring_soil_moisture") {
    soil_moisture_state = 0;
  }

  digitalWrite(light, light_state);
  digitalWrite(water_pump, water_pump_state);

  // Handle seed sowing/fertilizer servo (non-blocking)
  if (fertilizer_state == 1 || seed_sow_state == 1) {
    switch (seedSowCurrentState) {
      case IDLE:
        if (seedSowServo.read() != 90) {
          seedSowServo.write(90);
          seedSowLastTransition = currentMillis;
          seedSowCurrentState = WAIT_90;
        } else {
          seedSowCurrentState = MOVE_TO_180;
        }
        break;
      case MOVE_TO_90:
        seedSowServo.write(90);
        seedSowLastTransition = currentMillis;
        seedSowCurrentState = WAIT_90;
        break;
      case WAIT_90:
        if (currentMillis - seedSowLastTransition >= servoWaitTime) {
          seedSowCurrentState = MOVE_TO_180;
        }
        break;
      case MOVE_TO_180:
        if (seedSowServo.read() != 180) {
          seedSowServo.write(180);
          seedSowLastTransition = currentMillis;
          seedSowCurrentState = WAIT_180;
        } else {
          seedSowCurrentState = MOVE_TO_90; // Loop back to move to 90
        }
        break;
      case WAIT_180:
        if (currentMillis - seedSowLastTransition >= servoWaitTime) {
          seedSowCurrentState = MOVE_TO_90;
        }
        break;
    }
  } else {
    seedSowCurrentState = IDLE; // Reset state when not active
  }

  // Handle soil moisture measurement (non-blocking)
  if (soil_moisture_state == 1) {
    switch (soilMoistureCurrentState) {
      case INACTIVE:
        soilMoistureServoBig.write(40);
        soilMoistureLastTransition = currentMillis;
        soilMoistureCurrentState = WAIT_BIG_40;
        break;
      case MOVE_BIG_TO_40:
        soilMoistureServoBig.write(40);
        soilMoistureLastTransition = currentMillis;
        soilMoistureCurrentState = WAIT_BIG_40;
        break;
      case WAIT_BIG_40:
        if (currentMillis - soilMoistureLastTransition >= soilMoistureWaitTime) {
          soilMoistureCurrentState = MOVE_SMALL_TO_140;
        }
        break;
      case MOVE_SMALL_TO_140:
        soilMoistureServoSmall.write(140);
        soilMoistureLastTransition = currentMillis;
        soilMoistureCurrentState = WAIT_SMALL_140;
        break;
      case WAIT_SMALL_140:
        if (currentMillis - soilMoistureLastTransition >= soilMoistureWaitTime) {
          soilMoistureCurrentState = READ_SENSOR;
        }
        break;
      case READ_SENSOR:
        int soil_moisture_read = analogRead(soil_moisture_sensor);
        Serial.print("Soil Moisture: ");
        Serial.println(soil_moisture_read);
        lcd.setCursor(0, 0);
        lcd.print(soil_moisture_read);
        lcd.setCursor(1, 0);
        lcd.print("ShahratbhaiGJ");
        soilMoistureCurrentState = MOVE_BIG_TO_40; // Loop back to start
        break;
      default:
        soilMoistureCurrentState = MOVE_BIG_TO_40; // Fallback
        break;
    }
  } else {
    switch (soilMoistureCurrentState) {
      case INACTIVE:
      case MOVE_BIG_TO_90:
        soilMoistureServoBig.write(90);
        soilMoistureLastTransition = currentMillis;
        soilMoistureCurrentState = WAIT_BIG_90;
        break;
      case WAIT_BIG_90:
        if (currentMillis - soilMoistureLastTransition >= soilMoistureWaitTime) {
          soilMoistureCurrentState = MOVE_SMALL_TO_90;
        }
        break;
      case MOVE_SMALL_TO_90:
        soilMoistureServoSmall.write(90);
        soilMoistureLastTransition = currentMillis;
        soilMoistureCurrentState = WAIT_SMALL_90;
        break;
      case WAIT_SMALL_90:
        if (currentMillis - soilMoistureLastTransition >= soilMoistureWaitTime) {
          soilMoistureCurrentState = INACTIVE;
        }
        break;
      default:
        soilMoistureCurrentState = MOVE_BIG_TO_90; // Reset to move back
        break;
    }
  }
}