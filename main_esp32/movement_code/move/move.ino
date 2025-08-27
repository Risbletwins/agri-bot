#include <L298NX2.h>
#include <freertos/FreeRTOS.h>
#include <freertos/Task.h>
#include <HTTPClient.h>
#include <WiFi.h>

const char* ssid = "Ruslam";
const char* password = "10867000";

String serverName = "https://agri-bot-kwis.onrender.com/esp32-movement/";
String serverName2 = "https://agri-bot-kwis.onrender.com/esp32-receive/";
String response;
String response2;
int forDis;
int rowDis;
String main_instruction = "";
int feet = 1000;
int left_right_move_time = 1000;

const unsigned int EN_A = 19;
const unsigned int IN1_A = 22;
const unsigned int IN2_A = 21;

const unsigned int IN1_B = 18;
const unsigned int IN2_B = 17;
const unsigned int EN_B = 16;

unsigned int motorSpeedA = 255;
unsigned int motorSpeedB = 255;

L298NX2 all_motors(EN_A, IN1_A, IN2_A, EN_B, IN1_B, IN2_B);

void move_forward(unsigned long delaynow){
  Serial.println("going forward");
  all_motors.forward();
  delayMicroseconds(delaynow*1000);
  all_motors.stop();
}
void move_backward(unsigned long delaynow){
  Serial.println("going backward");
  all_motors.backward();
  delay(delaynow);
  all_motors.stop();

}
void move_right(int delaynow){
  Serial.println("going right");
  all_motors.forwardA();
  all_motors.backwardB();
  delay(delaynow);
  all_motors.stop();

}
void move_left(int delaynow){
  Serial.println("going left");
  all_motors.forwardB();
  all_motors.backwardA();
  delay(delaynow);
  all_motors.stop();

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
      }
    } else {
      HTTPClient http;
      HTTPClient http2;
      http.begin(serverName);
      http2.begin(serverName2);
      int httpResponseCode = http.GET();
      int httpResponseCode2 = http2.GET();
      if (httpResponseCode > 0) {
        // Serial.print("Response code: ");
        // Serial.println(httpResponseCode);
        response = http.getString();
        // Serial.println("Server response:");
        // Serial.println(response);
        int firstseparator = response.indexOf("-");
        int secondseparator = response.indexOf("_");
        String forwardDistance = response.substring(0,firstseparator);
        String leftrightdistance = response.substring(firstseparator+1,secondseparator);
        main_instruction = response.substring(secondseparator+1,response.length());
        forDis = (forwardDistance.toInt())*feet;
        rowDis = (leftrightdistance.toInt())*feet;
        // Serial.println(forDis);
        // Serial.println(rowDis);
        // Serial.println(main_instruction);
      } else {
        Serial.print("Error code: ");
        Serial.println(httpResponseCode);
      }
      if (httpResponseCode2 > 0) {
        response2 = http2.getString();
      } else {
        Serial.print("Error code: ");
        Serial.println(httpResponseCode2);
      }
      http.end();
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
    Serial.println("Rover Started.");
    for(int i = 0; main_instruction.length() > i; i++){
      char current_instruction = main_instruction[i];
      if(current_instruction == 'R'){
        move_right(left_right_move_time);
        Serial.println("Finished moving right");
        Serial.print("Duration:");
        Serial.println(left_right_move_time)
      }
      if(current_instruction == 'L'){
        move_left(left_right_move_time);
        Serial.println("Finished moving left");
        Serial.print("Duration:");
        Serial.println(left_right_move_time)
      }
      if(current_instruction == 'F'){
        move_forward(forDis);
        Serial.println("Finished moving forward");
        Serial.print("Duration:");
        Serial.println(forDis);
      }
      if(current_instruction == 'f'){
        move_forward(rowDis);
        Serial.println("Finished moving forward small");
        Serial.print("Duration:");
        Serial.println(rowDis);
      }
      if(response2 == "stop_rover"){
        Serial.println("Rover has been stopped.")
        all_motors.stop();
        break;
      }
    }
  }
  main_instruction = "";
}