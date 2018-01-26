#include <Arduino.h>


//Test Routine Program - By Stezipoo

#include <SoftPWMServo.h>
//#include <Servo.h>

//create servo objects
//Servo steering;
//Servo throttle;

const int PIN_STR = 9;
const int PIN_THR = 7;
const int PIN_IN_STR = 13;
const int PIN_IN_THR = 12;

//Servo ServoSTR;
//Servo ServoTHR;

void setup()
{
  Serial.begin(9600);
  delay(250);

  pinMode(PIN_IN_STR, INPUT);
  pinMode(PIN_IN_THR, INPUT);

  //pinMode(PIN_STR, OUTPUT);
  //pinMode(PIN_THR, OUTPUT);
  //ServoSTR.attach(PIN_STR);
  //ServoTHR.attach(PIN_THR);

}

/*
   printIMU to serial port
*/
void printData(float ax, float ay, float az, float gx, float gy, float gz, unsigned long time, int str, int thr )
{
  Serial.printf("%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%lu,%d,%d\n", ax, ay,  az, gx, gy, gz, millis(), str, thr);
}

void loop()
{
  //unsigned long THR_VAL = 0;
  unsigned long STR_VAL = pulseIn(PIN_IN_STR, HIGH, 25000); // Read the pulse width of
  unsigned long THR_VAL = pulseIn(PIN_IN_THR, HIGH, 25000); // each channel

  SoftPWMServoServoWrite(PIN_STR, STR_VAL);
  SoftPWMServoServoWrite(PIN_THR, THR_VAL);
  //ServoSTR.writeMicroseconds(STR_VAL);
  //ServoTHR.writeMicroseconds(THR_VAL);
  printData(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, millis(), STR_VAL, THR_VAL);
  delay(10);
}
