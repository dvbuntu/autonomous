#include <Arduino.h>
#include <Wire.h>
//#include <SoftPWMServo.h>
#include <Servo.h>

#define DEBUG_SERIAL 1

// IMU Define
#define    MPU9250_ADDRESS            0x68
#define    MAG_ADDRESS                0x0C

#define    GYRO_FULL_SCALE_250_DPS    0x00  
#define    GYRO_FULL_SCALE_500_DPS    0x08
#define    GYRO_FULL_SCALE_1000_DPS   0x10
#define    GYRO_FULL_SCALE_2000_DPS   0x18

#define    ACC_FULL_SCALE_2_G        0x00  
#define    ACC_FULL_SCALE_4_G        0x08
#define    ACC_FULL_SCALE_8_G        0x10
#define    ACC_FULL_SCALE_16_G       0x18

//AutoDrive 
#define MAX_CMD_BUF 17 
#define CMD_AUTO 0
#define CMD_STR 1
#define CMD_THR 2
#define CMD_TIME 3

const int PIN_STR = 9;
const int PIN_THR = 7;
const int PIN_IN_STR = 13;
const int PIN_IN_THR = 12;
const int PIN_AUTO_BTN = 15;

unsigned long last_serial_time;
unsigned long last_time;
boolean BLINK = true;

// shoot through delay
int PREV_DIR = LOW;
const int SHOOT_DELAY = 250;

Servo ServoSTR;
Servo ServoTHR;

// imu unit object
// This function read Nbytes bytes from I2C device at address Address. 
// Put read bytes starting at register Register in the Data array. 
void I2Cread(uint8_t Address, uint8_t Register, uint8_t Nbytes, uint8_t* Data)
{
  // Set register address
  Wire.beginTransmission(Address);
  Wire.write(Register);
  Wire.endTransmission();
  
  // Read Nbytes
  Wire.requestFrom(Address, Nbytes); 
  uint8_t index=0;
  while (Wire.available())
    Data[index++]=Wire.read();
}


// Write a byte (Data) in device (Address) at register (Register)
void I2CwriteByte(uint8_t Address, uint8_t Register, uint8_t Data)
{
  // Set register address
  Wire.beginTransmission(Address);
  Wire.write(Register);
  Wire.write(Data);
  Wire.endTransmission();
}

void setup() {
  Wire.begin();
  Serial.begin(9600);
  delay(250);

  pinMode(PIN_IN_STR, INPUT);
  pinMode(PIN_IN_THR, INPUT);
  pinMode(PIN_AUTO_BTN, INPUT);
  pinMode(PIN_LED1, OUTPUT);

  digitalWrite(PIN_LED1, LOW);

  ServoSTR.attach(PIN_STR);
  ServoTHR.attach(PIN_THR);

  // initIMU
  // Configure gyroscope range
  I2CwriteByte(MPU9250_ADDRESS,27,GYRO_FULL_SCALE_2000_DPS);
  // Configure accelerometers range
  I2CwriteByte(MPU9250_ADDRESS,28,ACC_FULL_SCALE_16_G);
  // Set by pass mode for the magnetometers
  I2CwriteByte(MPU9250_ADDRESS,0x37,0x02);
  
  // Request first magnetometer single measurement
  I2CwriteByte(MAG_ADDRESS,0x0A,0x01);

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
     Only need steering and throttle

     `auto 0/1, steering 1000-2000, thr amount 1000-2000, timestamp`
     1. steer 1000 - 2000
     2. throttle  1000 - 2000   When new line end
     execute the commands
     OUTPUT the results:
     auto, str, thr, millis, ???
*/
void doAutoCommands() {
  // http://arduino.stackexchange.com/questions/1013/how-do-i-split-an-incoming-string
  int cmd_cnt = 0;
  char cmdBuf[MAX_CMD_BUF + 1];

  int auton;
  int str;
  int thr;
  unsigned int time;

  byte size = Serial.readBytes(cmdBuf, MAX_CMD_BUF);
  cmdBuf[size] = 0;
  char *command = strtok(cmdBuf, ",");
  while (command != 0) {
    switch (cmd_cnt) {
    case CMD_AUTO:
      auton = atoi(command);	
      break;
    case CMD_STR:
      str = atoi(command);
      if (str > 2000 || str < 1000) {
        return;
      }
      if (DEBUG_SERIAL) {
        Serial.printf("%d, %d\n", cmd_cnt, str);
      }
      break;
    case CMD_THR:
      thr = atoi(command);
      if (thr > 2000 || thr < 1000) {
        return;
      }
      if (DEBUG_SERIAL) {
        Serial.printf("%d, %d\n", cmd_cnt, thr);
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
      return; // return if there are too many commands or non matching
    }
    command = strtok(0, ",");
    cmd_cnt++;

    if (cmd_cnt == 4) {
      if (DEBUG_SERIAL) {
        Serial.printf("str: %d, thr: %d, time: %lu\n", str, thr, time);
      }
      // do commands
      printData( millis(), str, thr);

      ServoSTR.writeMicroseconds(str);
      ServoTHR.writeMicroseconds(thr);
      if (DEBUG_SERIAL) {
	      Serial.printf("DONE COMMANDS: %lu, %lu\n", str, thr);
      }
    }
  }

  //delay(100);
  
}

void doAction() {

  unsigned long STR_VAL = pulseIn(PIN_IN_STR, HIGH, 25000); // Read pulse width of
  unsigned long THR_VAL = pulseIn(PIN_IN_THR, HIGH, 25000); // each channel

  // check if auto on
  if (digitalRead(PIN_AUTO_BTN) == true) {
    // Turn on when auto
    digitalWrite(PIN_LED1, HIGH);
    if (DEBUG_SERIAL) {
      Serial.println("FULL AUTO");
    }
    // auto mode is on
    // Check if command waiting
    if (Serial.available() > 0) {
      doAutoCommands();
    }
    return;
  } else if (STR_VAL == 0) // if no str data stop
  {                        // Turn off when not in auto
    if (DEBUG_SERIAL) {
      Serial.printf("Out of Range or Powered Off\n");
    } // Turn off when not in auto

    // set brake
    // kill the machine
    // pick a value that stops the car
    Serial.flush();
    ServoSTR.writeMicroseconds(1500);
    ServoTHR.writeMicroseconds(1500);
  } else {

    Serial.flush();
    ServoSTR.writeMicroseconds(STR_VAL);
    ServoTHR.writeMicroseconds(THR_VAL);
    printData( millis(), STR_VAL, THR_VAL);
  }
}
/*
   printIMU to serial port
*/
void printData(unsigned long time, int str, int thr) {
  // Serial.printf("%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%lu,%d,%d\n",
  //              ax, ay, az, gx, gy, gz, millis(), str, thr);

  // Read accelerometer and gyroscope
  uint8_t Buf[14];
  I2Cread(MPU9250_ADDRESS,0x3B,14,Buf);

  
  // Create 16 bits values from 8 bits data
  
  // Accelerometer
  int16_t ax=-(Buf[0]<<8 | Buf[1]);
  int16_t ay=-(Buf[2]<<8 | Buf[3]);
  int16_t az=Buf[4]<<8 | Buf[5];

  // Gyroscope
  int16_t gx=-(Buf[8]<<8 | Buf[9]);
  int16_t gy=-(Buf[10]<<8 | Buf[11]);
  int16_t gz=Buf[12]<<8 | Buf[13];
 
  // _____________________
  // :::  Magnetometer ::: 

  
  // Read register Status 1 and wait for the DRDY: Data Ready
  
  uint8_t ST1;
  do
  {
    I2Cread(MAG_ADDRESS,0x02,1,&ST1);
  }
  while (!(ST1&0x01));

  // Read magnetometer data  
  uint8_t Mag[7];  
  I2Cread(MAG_ADDRESS,0x03,7,Mag);
  

  // Create 16 bits values from 8 bits data
  
  // Magnetometer
  int16_t mx=-(Mag[3]<<8 | Mag[2]);
  int16_t my=-(Mag[1]<<8 | Mag[0]);
  int16_t mz=-(Mag[5]<<8 | Mag[4]);
  
 
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

void loop() {

  //doAction();

	if (Serial.available() > 0) {
		doAutoCommands();
	}

  //delay(10);
}
