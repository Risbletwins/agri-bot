#include <L298NX2.h>
#include <freertos/FreeRTOS.h>
#include <freertos/Task.h>

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
  delay(delaynow);
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
void printInfo(void*param){
  Serial.print("Motor A | Speed = ");
  Serial.print(all_motors.getSpeedA());
  Serial.print(" | Direction = ");
  Serial.print(all_motors.getDirectionA());

  Serial.print("Motor B | Speed = ");
  Serial.print(all_motors.getSpeedB());
  Serial.print(" | Direction = ");
  Serial.println(all_motors.getDirectionB());
  vTaskDelay(500/portTICK_PERIOD_MS);
}


void setup(){
  Serial.begin(115200);
  all_motors.setSpeedA(motorSpeedA);
  all_motors.setSpeedB(motorSpeedB);
}

void loop(){
  move_forward(2000);
  move_backward(2000);
  move_right(2000);
  move_left(2000);
}