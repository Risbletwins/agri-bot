#include <ESP32Servo.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

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

Servo solarPanelServo;
Servo soilMoistureServoBig;
Servo soilMoistureServoSmall;
Servo esp32CamXServo;
Servo esp32camYServo;
Servo seedSowServo;

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

String response = "";
String previous_response = response;

void seedSowTask(void *pvParameters) {
  while (1) {
    if (fertilizer_state == 1 || seed_sow_state == 1) {
      if (seedSowServo.read() != 90) {
        seedSowServo.write(90);
        vTaskDelay(500 / portTICK_PERIOD_MS);
      }
      if (seedSowServo.read() != 180) {
        seedSowServo.write(180);
        vTaskDelay(500 / portTICK_PERIOD_MS);
      }
    }
    vTaskDelay(200 / portTICK_PERIOD_MS); // Yield when idle
  }
}

void soilMoistureTask(void *pvParameters) {
  while (1) {
    if (soil_moisture_state == 1) {
      soilMoistureServoBig.write(40);
      vTaskDelay(1000 / portTICK_PERIOD_MS);
      soilMoistureServoSmall.write(140);
      vTaskDelay(1000 / portTICK_PERIOD_MS);
      int soil_moisture_read = analogRead(soil_moisture_sensor);
      Serial.print("Soil Moisture: ");
      Serial.println(soil_moisture_read);
    } else {
      soilMoistureServoBig.write(90);
      vTaskDelay(1000 / portTICK_PERIOD_MS);
      soilMoistureServoSmall.write(90);
      vTaskDelay(1000 / portTICK_PERIOD_MS);
    }
    vTaskDelay(200 / portTICK_PERIOD_MS); // Yield to reduce load
  }
}

void setup() {
  Serial.begin(115200);

  // Log reset reason
  Serial.print("Reset reason: ");
  Serial.println(esp_reset_reason());

  // Initialize WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    vTaskDelay(500 / portTICK_PERIOD_MS);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");

  // Initialize servos with explicit PWM timers
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  solarPanelServo.setPeriodHertz(50);
  soilMoistureServoBig.setPeriodHertz(50);
  soilMoistureServoSmall.setPeriodHertz(50);
  esp32CamXServo.setPeriodHertz(50);
  esp32camYServo.setPeriodHertz(50);
  seedSowServo.setPeriodHertz(50);

  // Check pin availability before attaching
  if (!solarPanelServo.attach(solar_panel_servo, 500, 2500)) {
    Serial.println("Failed to attach solarPanelServo (GPIO 26)");
  }
  if (!soilMoistureServoBig.attach(soil_moisture_servo_big, 500, 2500)) {
    Serial.println("Failed to attach soilMoistureServoBig (GPIO 33)");
  }
  if (!soilMoistureServoSmall.attach(soil_moisture_servo_small, 500, 2500)) {
    Serial.println("Failed to attach soilMoistureServoSmall (GPIO 25)");
  }
  if (!esp32CamXServo.attach(esp32cam_x_axis, 500, 2500)) {
    Serial.println("Failed to attach esp32CamXServo (GPIO 27)");
  }
  if (!esp32camYServo.attach(esp32cam_y_axis, 500, 2500)) {
    Serial.println("Failed to attach esp32camYServo (GPIO 14)");
  }
  if (!seedSowServo.attach(seed_sow_servo, 500, 2500)) {
    Serial.println("Failed to attach seedSowServo (GPIO 13)");
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

  // Create FreeRTOS tasks
  xTaskCreatePinnedToCore(
    seedSowTask,      // Task function
    "SeedSowTask",    // Task name
    2048,             // Stack size
    NULL,             // Parameter
    1,                // Priority
    NULL,             // Task handle
    1);               // Core 1

  xTaskCreatePinnedToCore(
    soilMoistureTask, // Task function
    "SoilMoistureTask", // Task name
    2048,             // Stack size
    NULL,             // Parameter
    1,                // Priority
    NULL,             // Task handle
    1);               // Core 1
}

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
        Serial.print("HTTP error code: ");
        Serial.println(httpResponseCode);
        WiFi.reconnect(); // Attempt reconnect on failure
      }
      http.end();
    } else {
      Serial.println("WiFi disconnected, reconnecting...");
      WiFi.reconnect();
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

  vTaskDelay(10 / portTICK_PERIOD_MS); // Yield to other tasks
}