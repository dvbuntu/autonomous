#include <Arduino.h>
#include "MPU9250.h"


//Test Routine Program - By Stezipoo

//#include <SoftPWMServo.h>
#include <Servo.h>

#define DEBUG_SERIAL 1

const int PIN_STR = 9;
const int PIN_THR = 7;
const int PIN_IN_STR = 13;
const int PIN_IN_THR = 12;

Servo ServoSTR;
Servo ServoTHR;

//imu unit object
MPU9250 ottoIMU;

int initIMU() {
  // Read the WHO_AM_I register, this is a good test of communication
  byte addr = ottoIMU.readByte(MPU9250_ADDRESS, WHO_AM_I_MPU9250);
  if (addr == 0x71) // WHO_AM_I should always be 0x68
  {
    if (DEBUG_SERIAL) {
      Serial.println("MPU9250 is online...");
    }
    ottoIMU.MPU9250SelfTest(ottoIMU.SelfTest);
    // Calibrate gyro and accelerometers, load biases in bias registers
    ottoIMU.calibrateMPU9250(ottoIMU.gyroBias, ottoIMU.accelBias);
    ottoIMU.initMPU9250();
    // Initialize device for active mode read of acclerometer, gyroscope, and
    // temperature
    if (DEBUG_SERIAL) {
      Serial.println("MPU9250 initialized for active data mode....");
    }
    // Read the WHO_AM_I register of the magnetometer, this is a good test of
    // communication
    byte maddr = ottoIMU.readByte(AK8963_ADDRESS, WHO_AM_I_AK8963);
    if (DEBUG_SERIAL) {
      Serial.printf("AK8963 I AM %02x  I should be %02x \n", maddr, 0x48);
    }
    // Get magnetometer calibration from AK8963 ROM
    ottoIMU.initAK8963(ottoIMU.magCalibration);
    // Initialize device for active mode read of magnetometer
    if (DEBUG_SERIAL) {
      Serial.println("AK8963 initialized for active data mode....");
    }
  }
  else
  {
    if (DEBUG_SERIAL) {
      Serial.printf("Could not connect to MPU9250: 0x %02x\n", addr);
    }
    //while (1) ; // Loop forever if communication doesn't happen
    return false;
  }
  return true;
}

void setup()
{
  Serial.begin(9600);
  delay(250);

  pinMode(PIN_IN_STR, INPUT);
  pinMode(PIN_IN_THR, INPUT);

  //pinMode(PIN_STR, OUTPUT);
  //pinMode(PIN_THR, OUTPUT);
  ServoSTR.attach(PIN_STR);
  ServoTHR.attach(PIN_THR);


}

/*
   printIMU to serial port
*/
void printData(float ax, float ay, float az, float gx, float gy, float gz, unsigned long time, int str, int thr )
{

 // Serial.printf("%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%lu,%d,%d\n",
 //               ax, ay,  az, gx, gy, gz, millis(), str, thr);
  Serial.print(ax);
  Serial.print(",");
  Serial.print(ay);
  Serial.print(",");
  Serial.print(az);
  Serial.print(",");
  Serial.print(gx);
  Serial.print(",");
  Serial.print(gy);
  Serial.print(",");
  Serial.print(gz);
  Serial.print(",");
  Serial.print(millis());
  Serial.print(",");
  Serial.print(str);
  Serial.print(",");
  Serial.print(thr);
  Serial.println();

}


void loop()
{
  unsigned long STR_VAL = pulseIn(PIN_IN_STR, HIGH, 25000); // Read the pulse width of
  unsigned long THR_VAL = pulseIn(PIN_IN_THR, HIGH, 25000); // each channel

  //SoftPWMServoServoWrite(PIN_STR, STR_VAL);
  ServoSTR.writeMicroseconds(STR_VAL);
  ServoTHR.writeMicroseconds(THR_VAL);

  ottoIMU.readAccelData(ottoIMU.accelCount);  // Read the x/y/z adc values
  ottoIMU.getAres();
  ottoIMU.ax = (float)ottoIMU.accelCount[0] * ottoIMU.aRes; // - accelBias[0];
  ottoIMU.ay = (float)ottoIMU.accelCount[1] * ottoIMU.aRes; //   accelBias[1];
  ottoIMU.az = (float)ottoIMU.accelCount[2] * ottoIMU.aRes; // - accelBias[2];
  ottoIMU.readGyroData(ottoIMU.gyroCount);  // Read the x/y/z adc values
  ottoIMU.getGres();
  ottoIMU.gx = (float)ottoIMU.gyroCount[0] * ottoIMU.gRes;
  ottoIMU.gy = (float)ottoIMU.gyroCount[1] * ottoIMU.gRes;
  ottoIMU.gz = (float)ottoIMU.gyroCount[2] * ottoIMU.gRes;

  // Serial.printf("%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%lu,%d,%d\n", ottoIMU.ax, ottoIMU.ay,  ottoIMU.az, ottoIMU.gx, ottoIMU.gy, ottoIMU.gz, millis(),


  printData(ottoIMU.ax, ottoIMU.ay,  ottoIMU.az, ottoIMU.gx, ottoIMU.gy, ottoIMU.gz, millis(), STR_VAL, THR_VAL);
  delay(10);
}
