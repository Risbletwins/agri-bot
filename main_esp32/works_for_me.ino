#include <ESP32Servo.h>
#include <Wire.h>
// #include <LiquidCrystal_I2C.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

#define solar_panel_servo 26
#define soil_moisture_servo_big 13
#define soil_moisture_servo_small 25
#define seed_sow_servo 33

#define soil_moisture_sensor 35
#define voltage_sensor_solar_panel 39
#define voltage_sensor_battery 34
#define water_pump 2
#define ldr_sensor 36
#define light 0
#define humidity_sensor 32
// #define lcd_SDA 21
// #define lcd_SCL 22

Servo solarPanelServo;
Servo soilMoistureServoBig;
Servo soilMoistureServoSmall;
Servo seedSowServo;

// LiquidCrystal_I2C lcd(0x27, 20, 4);

int light_state = 0;
int fertilizer_state = 0;
int seed_sow_state = 0;
int water_pump_state = 0;
int soil_moisture_state = 0;

const char* ssid = "Ruslam";
const char* password = "10867000";
const char* serverName = "https://agri-bot-kwis.onrender.com/esp32-receive/";

unsigned long previousMillis = 0;
const long interval = 1000;

String response = "";
String previous_response = response;
SemaphoreHandle_t i2cMutex = NULL;


void seedSowTask(void *pvParameters) {
  for(;;){
    if (fertilizer_state == 1 || seed_sow_state == 1) {
      Serial.println("seed sow has started.");
      if (seedSowServo.read() != 90) {
        seedSowServo.write(90);
        vTaskDelay(500 / portTICK_PERIOD_MS);
      }
      if (seedSowServo.read() != 180) {
        seedSowServo.write(180);
        vTaskDelay(500 / portTICK_PERIOD_MS);
      }
    } else {
      Serial.println("seed sow has ended.");
      vTaskDelay(100 / portTICK_PERIOD_MS); 
    }
  }
}

void soilMoistureTask(void *pvParameters) {
  for (;;) {
    if (soil_moisture_state == 1) {
      Serial.println("The soil Moisture measuring has started.");
      soilMoistureServoBig.write(40);
      vTaskDelay(1000 / portTICK_PERIOD_MS);
      soilMoistureServoSmall.write(140);
      vTaskDelay(1000 / portTICK_PERIOD_MS);
      int soil_moisture_read = analogRead(soil_moisture_sensor);
      Serial.print("Soil Moisture: ");
      Serial.println(soil_moisture_read);
      
      if (xSemaphoreTake(i2cMutex, pdMS_TO_TICKS(1000)) == pdTRUE) {
        // lcd.setCursor(0, 1);
        // lcd.print("                "); 
        // lcd.setCursor(0, 1);
        // lcd.print(soil_moisture_read);
        // lcd.setCursor(0, 0);
        // lcd.print("Soil Moisture Read:");
        Serial.println("LCD is Showing.");
        xSemaphoreGive(i2cMutex);
      } else {
        Serial.println("Failed to acquire I2C mutex");
      }
    } else {
      Serial.println("The soil Moisture measuring has stopped.");
      soilMoistureServoBig.write(90);
      vTaskDelay(1000 / portTICK_PERIOD_MS);
      soilMoistureServoSmall.write(90);
      vTaskDelay(1000 / portTICK_PERIOD_MS);
    }
    vTaskDelay(100 / portTICK_PERIOD_MS);
    UBaseType_t uxHighWaterMark = uxTaskGetStackHighWaterMark(NULL);
    Serial.print("soilMoistureTask stack high water mark: ");
    Serial.println(uxHighWaterMark);
  }
}
void wifi_run(void* param) {
  WiFi.begin(ssid, password);
  Serial.print("connecting to wifi");
  int retryCount = 0;
  const int maxRetries = 20; 
  for (;;) {
    if (WiFi.status() != WL_CONNECTED) {
      if (retryCount < maxRetries) {
        Serial.print(".");
        vTaskDelay(500 / portTICK_PERIOD_MS);
        retryCount++;
      } else {
        Serial.println("WiFi connection failed, retrying...");
        WiFi.disconnect();
        WiFi.begin(ssid, password);
        retryCount = 0;
        vTaskDelay(5000 / portTICK_PERIOD_MS);
      }
    } else {
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
      vTaskDelay(1000 / portTICK_PERIOD_MS);
      retryCount = 0;
    }
  }
}


void setup() {
  Serial.begin(115200);

  i2cMutex = xSemaphoreCreateMutex();
  if (i2cMutex == NULL) {
    Serial.println("Failed to create I2C mutex");
  }

  xTaskCreatePinnedToCore(
    wifi_run,
    "wifi run",
    4096,
    NULL,
    2,
    NULL,
    0
  );

  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  solarPanelServo.setPeriodHertz(50);
  soilMoistureServoBig.setPeriodHertz(50);
  soilMoistureServoSmall.setPeriodHertz(50);
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
  if (!seedSowServo.attach(seed_sow_servo, 500, 2500)) {
    Serial.println("Failed to attach seedSowServo... what a pain..");
  }

  solarPanelServo.write(0);
  soilMoistureServoBig.write(0);
  soilMoistureServoSmall.write(0);
  seedSowServo.write(90);

  pinMode(voltage_sensor_solar_panel, INPUT);
  pinMode(voltage_sensor_battery, INPUT);
  pinMode(humidity_sensor, INPUT);
  pinMode(ldr_sensor, INPUT);
  pinMode(soil_moisture_sensor, INPUT);
  pinMode(water_pump, OUTPUT);
  pinMode(light, OUTPUT);

  // Wire.begin(lcd_SDA, lcd_SCL);
  // Wire.setClock(100000);
  // lcd.init();
  // lcd.backlight();

  xTaskCreatePinnedToCore(
    seedSowTask,      
    "SeedSowTask",    
    2048,            
    NULL,             
    2,                
    NULL,             
    1);               

  xTaskCreatePinnedToCore(
    soilMoistureTask, 
    "SoilMoistureTask", 
    4096, 
    NULL,             
    2,                
    NULL,             
    1);               
}



void loop() {


  if (response == "light_on") {
    light_state = HIGH;
    Serial.println("light has been turned on.");
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

  vTaskDelay(10 / portTICK_PERIOD_MS);
}