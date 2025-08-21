#include <Servo.h>
#include <Wire.h>
#include <ESP32Servo.h>
#include <LiquidCrystal_I2C.h>



#define solar_panel_servo 32 //o

#define soil_moisture_servo_big 33 //o
#define soil_moisture_servo_small 25 //o
#define soil_moisture_sensor 36 //i

#define esp32cam_x_axis 27 //o
#define esp32cam_y_axis 14 //o
 
#define seed_sow_servo 12 //o

#define voltage_sensor_solar_panel 39 //i
#define voltage_sensor_battery 34 //i

#define water_pump 13 //o
#define ldr_sensor 35 //i

#define humidity_sensor 19 //i

#define lcd_SDA 21 //o
#define lcd_SCL 22 //o


Servo solarPanelServo
Servo soilMoistureServoBig
Servo soilMoistureServoSmall
Servo esp32CamXServo
Servo esp32camYServo
Servo seedSowServo

LiquidCrystal_I2C lcd (0x27, 20, 4);
Servo servoS; 
int pos = 90; 

void setup() {
  Wire.begin(lcd_SDA, lcd_SCL);
  lcd.init();
  lcd.backlight();
  lcd.print("Hello ESP32");
}

void loop() {
  lcd.setCursor(1, 0);
  lcd.print("Seed Sowing");
  { 
    servoS.write(180);             
    delay(400);                      
  }
  { 
    servoS.write(pos);             
    delay(400);                       
  }
}