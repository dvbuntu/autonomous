#include <Arduino.h>
#include "MPU9250.h"


//Test Routine Program - By Stezipoo

//#include <SoftPWMServo.h>
#include <Servo.h>

#define DEBUG_SERIAL 1
#define MAX_CMD_BUF  40

const int PIN_STR = 9;
const int PIN_THR = 7;
const int PIN_IN_STR = 13;
const int PIN_IN_THR = 12;
const int PIN_KILL = 23;


/*
    Automatic Set Up
*/
#define MAX_CMD_BUF  20
#define CMD_STR 0
#define CMD_DIR 1
#define CMD_GAS 2
#define CMD_TIME 3

#define THR_DIR 0
#define THR_THR 1

unsigned long last_serial_time;
unsigned long last_time;
boolean BLINK = true;


//shoot through delay
int PREV_DIR = LOW;
const int SHOOT_DELAY = 250;

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
  Wire.begin();
  Serial.begin(9600);
  delay(250);

  pinMode(PIN_IN_STR, INPUT);
  pinMode(PIN_IN_THR, INPUT);
  pinMode(PIN_LED1, OUTPUT);

  pinMode(PIN_KILL, OUTPUT);
  digitalWrite(PIN_LED1, LOW);
  digitalWrite(PIN_KILL, LOW);
  //pinMode(PIN_STR, OUTPUT);
  //pinMode(PIN_THR, OUTPUT);
  ServoSTR.attach(PIN_STR);
  ServoTHR.attach(PIN_THR);

  initIMU();

}





/*
   Find and do the autonmous commands
   /*
     read entire input max length
     while more serial
     fill the comdBuf until a ','
     cmds
     Output:
     `accel_x, accel_y, accel_z, yaw, pitch, roll,time`.
     Input Commands:
     `steering 0-255, direction 0/1, gas amount 0-255, timestamp`
     1. steer 0-255 maps to
     2. direction
     3. gas
     4. time stamp
     When new line end
     execute the commands

     255,1,255,1110000
     255,0,0,1110001
*/
void doAutoCommands() {


  //http://arduino.stackexchange.com/questions/1013/how-do-i-split-an-incoming-string
  int cmd_cnt = 0;
  char cmdBuf [MAX_CMD_BUF + 1];

  int str;
  int dir;
  int gas;
  unsigned int time;



  byte size = Serial.readBytes(cmdBuf, MAX_CMD_BUF);
  cmdBuf[size] = 0;
  char* command = strtok(cmdBuf, ",");
  while (command != 0) {
    switch (cmd_cnt) {
      case CMD_STR:
        str = atoi(command);
        if (str > 255 || str < 0) {
          return;
        }
        if (DEBUG_SERIAL) {
          Serial.printf("%d, %d\n", cmd_cnt, str);
        }
        break;
      case CMD_DIR:
        dir = atoi(command);
        if (dir == 1) {
          dir = 0;
        } else {
          dir = 1;
        }
        if (dir  < 0  || dir > 1) {
          return;
        }
        if (DEBUG_SERIAL) {
          Serial.printf("%d, %d\n", cmd_cnt, dir );
        }
        break;
      case CMD_GAS:
        gas = atoi(command);
        if (gas > 255 || gas < 0) {
          return;
        }
        if (DEBUG_SERIAL) {
          Serial.printf("%d, %d\n", cmd_cnt, gas);
        }
        break;
      case CMD_TIME:
        time = atoi(command);
        /*
            Remove time check
          if (time < last_time) {
          return;
          }
        */
        last_time = time;
        if (DEBUG_SERIAL) {
          Serial.printf("%d, %lu\n", cmd_cnt, time);
        }
        break;
      default:
        if (DEBUG_SERIAL) {
          Serial.println("NOOP");
        }
        return; //return if there are too many commands or non matching
    }
    command = strtok(0, ",");
    cmd_cnt++;

    if (cmd_cnt == 4) {
      if (DEBUG_SERIAL) {
        Serial.printf("str: %d, dir: %d, gas: %d, time: %lu\n", str, dir, gas, time);
      }
      //do commands
      //autoSteer(str);
      //autoThrottle(dir, gas);
      //autoRearSteer(str, dir, gas);
    }
  }

  delay(100);
  if (DEBUG_SERIAL) {
    Serial.printf("DONE COMMANDS: %lu\n", millis());
  }
}


void doAction() {


  unsigned long STR_VAL = pulseIn(PIN_IN_STR, HIGH, 25000); // Read the pulse width of
  unsigned long THR_VAL = pulseIn(PIN_IN_THR, HIGH, 25000); // each channel

  //check for kill switch
  if (ch[CH_KILL] > 1500 ) {
    digitalWrite(PIN_KILL, HIGH);
    if (DEBUG_SERIAL) {
      Serial.println("KILL HIGH");
    }
  }
  else {
    digitalWrite(PIN_KILL, LOW);
  }//end kill switch

  //check if auto on
  if (ch[CH_AUTO] > 1500 && ch[CH_AUTO] < 1900) {
    //Turn on when auto
    digitalWrite(PIN_LED1, HIGH);
    if (DEBUG_SERIAL) {
      Serial.println("FULL AUTO");
    }
    //auto mode is on
    //Check if command waiting
    if (Serial.available() > 0) {
      doAutoCommands();
    }
    if (ch[CH_AUTO] > 1900)
    {
      autoSpin();
    }
    return;
  }
  else if (ch[CH_STR] == 0 ) //check for RCCommands
  {
    Serial.flush();

    //Turn off when not in auto
    if (DEBUG_SERIAL) {
      Serial.printf("Out of Range or Powered Off\n");
    }
    //set brake
    //kill the machine
  }
  else
  {

    Serial.flush();
    ServoSTR.writeMicroseconds(STR_VAL);
    ServoTHR.writeMicroseconds(THR_VAL);

  }
}





/*
   printIMU to serial port
*/
void printData(float ax, float ay, float az, float gx, float gy, float gz, unsigned long time, int str, int thr )
{

  Serial.printf("%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%lu,%d,%d\n",
                ax, ay,  az, gx, gy, gz, millis(), str, thr);

}


void loop()
{

  doAction();

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
