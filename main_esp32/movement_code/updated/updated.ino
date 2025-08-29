#include <L298NX2.h>
#include <freertos/FreeRTOS.h>
#include <freertos/Task.h>
#include <HTTPClient.h>
#include <WiFi.h>

const char* ssid = "SHAHRAT (2.4G)";
const char* password = "66667777";

String serverName = "https://agri-bot-kwis.onrender.com/esp32-movement/";
String serverName2 = "https://agri-bot-kwis.onrender.com/esp32-receive/";
String response;
String response2;
int forDis;
int rowDis;
String main_instruction = "";
int feet = 100;  // ms per foot - calibrate: measure distance traveled in 1000ms and adjust (e.g., if 0.5 feet, set to 2000)
int left_right_move_time = 1500;  // ms for a 90-degree turn - calibrate by timing a full turn
int stop_delay = 2000;  // ms pause after each move - reduce if movements feel too jerky/slow

const unsigned int EN_A = 19;
const unsigned int IN1_A = 22;
const unsigned int IN2_A = 21;

const unsigned int IN1_B = 18;
const unsigned int IN2_B = 17;
const unsigned int EN_B = 16;

unsigned int motorSpeedA = 255;
unsigned int motorSpeedB = 255;

L298NX2 all_motors(EN_A, IN1_A, IN2_A, EN_B, IN1_B, IN2_B);

void move_forward(int delaynow){
  Serial.println("Forward");
  all_motors.forward();
  delay(delaynow);
  all_motors.stop();
  delay(stop_delay);
}
void move_backward(int delaynow){
  Serial.println("Backward");
  all_motors.backward();
  delay(delaynow);
  all_motors.stop();
  delay(stop_delay);
}
void move_right(int delaynow){
  Serial.println("Right");
  all_motors.forwardA();
  all_motors.backwardB();
  delay(delaynow);
  all_motors.stop();
  delay(stop_delay);
}
void move_left(int delaynow){
  Serial.println("Left");
  all_motors.forwardB();
  all_motors.backwardA();
  delay(delaynow);
  all_motors.stop();
  delay(stop_delay);
}

void wifi_run(void* param) {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to Wifi");
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
      }
    } else {
      HTTPClient http;
      HTTPClient http2;
      http.setTimeout(3000);  // Set timeout to avoid hangs
      http2.setTimeout(3000);
      http.begin(serverName);
      http2.begin(serverName2);
      int httpResponseCode = http.GET();
      int httpResponseCode2 = http2.GET();
      if (httpResponseCode > 0) {
        response = http.getString();
        response.trim();  // Remove any whitespace
        int firstseparator = response.indexOf("-");
        int secondseparator = response.indexOf("_");
        if (firstseparator > 0 && secondseparator > firstseparator) {
          String forwardDistance = response.substring(0, firstseparator);
          String leftrightdistance = response.substring(firstseparator + 1, secondseparator);
          main_instruction = response.substring(secondseparator + 1);
          if (forwardDistance.toInt() > 0 && leftrightdistance.toInt() > 0) {  // Basic validation
            forDis = forwardDistance.toInt() * feet;
            rowDis = leftrightdistance.toInt() * feet;
            Serial.println("Parsed distances: forDis=" + String(forDis) + ", rowDis=" + String(rowDis));
            Serial.println("Instruction: " + main_instruction);
          } else {
            Serial.println("Invalid distances in response");
            main_instruction = "";  // Skip processing
          }
        } else {
          Serial.println("Invalid response format");
          main_instruction = "";
        }
      } else {
        Serial.print("Error code: ");
        Serial.println(httpResponseCode);
      }
      if (httpResponseCode2 > 0) {
        response2 = http2.getString();
        response2.trim();
      } else {
        Serial.print("Error code: ");
        Serial.println(httpResponseCode2);
      }
      http.end();
      http2.end();  // Close the second client too
      vTaskDelay(1000 / portTICK_PERIOD_MS);
      retryCount = 0;
    }
  }
}

void setup(){
  Serial.begin(115200);
  all_motors.setSpeedA(motorSpeedA);
  all_motors.setSpeedB(motorSpeedB);
  xTaskCreatePinnedToCore(
    wifi_run,
    "wifi run",
    4096,
    NULL,
    2,
    NULL,
    0
  );
}

void loop(){
  if(response2 == "start_rover"){
    // Snapshot globals to avoid race conditions during processing
    String local_instruction = main_instruction;
    int local_forDis = forDis;
    int local_rowDis = rowDis;
    for(int i = 0; i < local_instruction.length(); i++){
      char current_instruction = local_instruction[i];
      if(current_instruction == 'R'){
        move_right(left_right_move_time);
        Serial.println("Finished Moving Right");
        Serial.print("Duration:");
        Serial.println(left_right_move_time);
      }
      else if(current_instruction == 'L'){
        move_left(left_right_move_time);
        Serial.println("Finished Moving Left");
        Serial.print("Duration:");
        Serial.println(left_right_move_time);
      }
      else if(current_instruction == 'F'){
        move_forward(local_forDis);
        Serial.println("Finished Moving Forward");
        Serial.print("Duration:");
        Serial.println(local_forDis);
      }
      else if(current_instruction == 'f'){
        move_forward(local_rowDis);
        Serial.println("Finished Moving Forward Small");
        Serial.print("Duration:");
        Serial.println(local_rowDis);
      }
      else {
        Serial.print("Unknown command: ");
        Serial.println(current_instruction);
      }
      if(response2 == "stop_rover"){
        Serial.println("Rover has been stopped.");
        all_motors.stop();
        break;
      }
    }
    main_instruction = "";  // Clear after processing
  }
}