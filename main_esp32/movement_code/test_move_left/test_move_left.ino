#include <L298NX2.h>

const unsigned int EN_A = 19;
const unsigned int IN1_A = 22;
const unsigned int IN2_A = 21;

const unsigned int IN1_B = 18;
const unsigned int IN2_B = 17;
const unsigned int EN_B = 16;

unsigned int motorSpeedA = 255;
unsigned int motorSpeedB = 255;

L298NX2 all_motors(EN_A, IN1_A, IN2_A, EN_B, IN1_B, IN2_B);

int left_right_move_time = 1500;  // ms for the turn - adjust this value, re-upload, and observe if it's ~90 degrees
int stop_delay = 2000;  // ms pause after the move

void move_left(int delaynow){
  Serial.println("Turning Left");
  all_motors.forwardB();
  all_motors.backwardA();
  delay(delaynow);
  all_motors.stop();
  delay(stop_delay);
}

void setup(){
  Serial.begin(115200);
  all_motors.setSpeedA(motorSpeedA);
  all_motors.setSpeedB(motorSpeedB);
  
  // Automatically start moving left on boot
  Serial.println("Starting left turn calibration with delay: " + String(left_right_move_time) + " ms");
  move_left(left_right_move_time);
  Serial.println("Turn complete. Adjust left_right_move_time in code and re-upload to test again.");
}

void loop(){
  // Empty - no repeated actions
  move_left(left_right_move_time);
}