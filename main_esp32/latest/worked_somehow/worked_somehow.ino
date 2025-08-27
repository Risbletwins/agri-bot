#include <ESP32Servo.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <DHT11.h>

DHT11 dht11(32);

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
#define lcd_SDA 21
#define lcd_SCL 22
#define fertilizer_motor 26

Servo solarPanelServo;
Servo soilMoistureServoBig;
Servo soilMoistureServoSmall;
Servo seedSowServo;

LiquidCrystal_I2C lcd(0x27, 20, 4);

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

bool lcd_connected = false;

bool isI2CDevicePresent(uint8_t address) {
  Wire.beginTransmission(address);
  int error = Wire.endTransmission();
  return (error == 0);
}

void lcd_on(void* param) {
  for (;;) {
    int temperature = dht11.readTemperature();
    int humidity = dht11.readHumidity();
    int voltage_sensor_battery_read = analogRead(voltage_sensor_battery);
    
    if (lcd_connected) {
      if (xSemaphoreTake(i2cMutex, pdMS_TO_TICKS(1000)) == pdTRUE) {
        lcd.clear(); // Clear to avoid overlap with other tasks
        lcd.setCursor(0, 0);
        lcd.print("Temp: ");
        lcd.print(temperature);
        lcd.print("C");
        lcd.setCursor(0, 1);
        lcd.print("Humidity: ");
        lcd.print(humidity);
        lcd.print("%");
        lcd.setCursor(0, 2);
        lcd.print("Voltage: ");
        lcd.print(voltage_sensor_battery_read);
        xSemaphoreGive(i2cMutex);
      } else {
        Serial.println("Failed to acquire I2C mutex in lcd_on");
      }
    } else {
      Serial.print("Temp: ");
      Serial.print(temperature);
      Serial.println("C");
      Serial.print("Humidity: ");
      Serial.print(humidity);
      Serial.println("%");
      Serial.print("Voltage: ");
      Serial.println(voltage_sensor_battery_read);
    }
    
    vTaskDelay(1000 / portTICK_PERIOD_MS); // Update every 1 second
  }
}

void seedSowTask(void *pvParameters) {

  for (;;) {
    if (seed_sow_state == 1) {
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
      
      if (lcd_connected) {
        if (xSemaphoreTake(i2cMutex, pdMS_TO_TICKS(1000)) == pdTRUE) {
          lcd.setCursor(0, 3); // Use line 3 to avoid overlap with lcd_on
          lcd.print("                "); 
          lcd.setCursor(0, 3);
          lcd.print("SoilMos: ");
          lcd.print(soil_moisture_read);
          Serial.println("LCD is Showing.");
          xSemaphoreGive(i2cMutex);
        } else {
          Serial.println("Failed to acquire I2C mutex");
        }
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
  soilMoistureServoBig.setPeriodHertz(50);
  soilMoistureServoSmall.setPeriodHertz(50);
  seedSowServo.setPeriodHertz(50);

  if (!soilMoistureServoBig.attach(soil_moisture_servo_big, 500, 2500)) {
    Serial.println("Failed to attach soilMoistureServoBig... what a pain..");
  }
  if (!soilMoistureServoSmall.attach(soil_moisture_servo_small, 500, 2500)) {
    Serial.println("Failed to attach soilMoistureServoSmall... what a pain..");
  }
  if (!seedSowServo.attach(seed_sow_servo, 500, 2500)) {
    Serial.println("Failed to attach seedSowServo... what a pain..");
  }

  soilMoistureServoBig.write(0);
  soilMoistureServoSmall.write(0);
  seedSowServo.write(90);

  pinMode(voltage_sensor_solar_panel, INPUT);
  pinMode(voltage_sensor_battery, INPUT);
  pinMode(humidity_sensor, INPUT);
  pinMode(ldr_sensor, INPUT);
  pinMode(soil_moisture_sensor, INPUT);
  pinMode(water_pump, OUTPUT);

  Wire.begin(lcd_SDA, lcd_SCL);
  Wire.setClock(100000);
  lcd_connected = isI2CDevicePresent(0x27);
  if (lcd_connected) {
    lcd.init();
    lcd.backlight();
  } else {
    Serial.println("LCD not detected, skipping initialization and usage.");
  }

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

  xTaskCreatePinnedToCore(
    lcd_on,        
    "LCD On",      
    2048,          
    NULL,          
    2,             
    NULL,          
    1              
  );
}

void loop() {

  if (response == "fertilizer_on") {
    fertilizer_state = HIGH;
  } else if (response == "fertilizer_off") {
    fertilizer_state = LOW;
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
  digitalWrite(water_pump, water_pump_state);
  digitalWrite(fertilizer_motor, fertilizer_state);

  vTaskDelay(1 / portTICK_PERIOD_MS);
}