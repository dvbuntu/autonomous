/*
    OTTO REmote Drive:
    Drive the oTTO Tractor with a Remote RC Controller
   by Rick Anderson (ricklon)

*/
#include <Arduino.h>
#include <SoftPWMServo.h>
#include <Wire.h>

#define DEBUG_SERIAL false
#define MAX_CMD_BUF  17


/*
  Define IMU mpu9250 values

*/
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

#define WHO_AM_I_MPU9250 0x75 // Should return 0x71


/*
   Setup RC Controller
   What are the channels:
   0: thr: throttle
   1: str, steering
   2: kill: pos1: OK, pos:2 Emergency Stop
   3: auto: pos1: Manual, pos: AUTO

*/

#define CH_STR 0
#define CH_THR 1
#define CH_KILL 2
#define CH_AUTO 3

const int channels = 4;
int ch[channels];
int chmin[channels];
int chmid[channels];
int chmax[channels];

/*
    Automatic Set Up
*/
#define CMD_AUTO 0
#define CMD_STR 1
#define CMD_THR 2
#define CMD_TIME 3

#define THR_DIR 0
#define THR_THR 1

unsigned long last_serial_time;
unsigned long last_time;
boolean BLINK = true;

//Setup Motor Controller
const int PIN_M1_DIR = 14;
const int PIN_M2_DIR = 3;
const int PIN_M1_PWM = 4;
const int PIN_M2_PWM = 7;
const int PIN_KILL = 23;

//Setup Steering Control
const int PIN_STR = 10;

//shoot through delay
int PREV_DIR = LOW;
const int SHOOT_DELAY = 250;

int thrData[2] = {0, 0};

int log_thr = 0;
int log_steer = 0;

unsigned long steer_history[10];
int steer_next_ind;


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


int initIMU() {
  // Set accelerometers low pass filter at 5Hz
  I2CwriteByte(MPU9250_ADDRESS,29,0x06);
  // Set gyroscope low pass filter at 5Hz
  I2CwriteByte(MPU9250_ADDRESS,26,0x06);
 
  
  // Configure gyroscope range
  I2CwriteByte(MPU9250_ADDRESS,27,GYRO_FULL_SCALE_1000_DPS);
  // Configure accelerometers range
  I2CwriteByte(MPU9250_ADDRESS,28,ACC_FULL_SCALE_4_G);
  // Set by pass mode for the magnetometers
  I2CwriteByte(MPU9250_ADDRESS,0x37,0x02);
  // Request continuous magnetometer measurements in 16 bits
  I2CwriteByte(MAG_ADDRESS,0x0A,0x16);
}

void doAction() {
  ch[CH_STR] = pulseIn(A1, HIGH, 25000); // Read the pulse width of
  ch[CH_THR] = pulseIn(A2, HIGH, 25000); // each channel
  ch[CH_KILL] = pulseIn(A3, HIGH, 25000);
  ch[CH_AUTO] = pulseIn(A4, HIGH, 25000);
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
    if (ch[CH_AUTO] > 2000)
    {
      if (DEBUG_SERIAL) 
      {
      Serial.printf("Greater than 2000\n");
      }
    }
    return;
  }
  else if (ch[CH_STR] == 0 ) //check for RCCommands
  {
    Serial.flush();
    //char cmdBuf [MAX_CMD_BUF + 1];
    //byte size = Serial.readBytes(cmdBuf, MAX_CMD_BUF);
    //Turn off when not in auto
    //digitalWrite(PIN_LED1, HIGH);
    if (DEBUG_SERIAL) {
      Serial.printf("Out of Range or Powered Off\n");
    }
    //set brake
    //kill the machine
  }
  else
  {
    //empty  serial buffer
    //char cmdBuf [MAX_CMD_BUF + 1];
    //byte size = Serial.readBytes(cmdBuf, MAX_CMD_BUF);
    Serial.flush();
    /*
       steering 1100 - 1500 map left
       steering between 1500 - 1600 straight
        steering 1600 - 1900 map left
    */
   // digitalWrite(PIN_LED1, HIGH);
    steer_history[steer_next_ind]=ch[CH_STR];
    steer_next_ind=(steer_next_ind+1)%10;
    unsigned long filt_str_val=compAvg(steer_history, 10);
    ch[CH_STR]=int(filt_str_val);
    setSteering(ch[CH_STR]);
    /*
       Throttling:
        1100 - 1500: reverse
        1500 - 1600: no throttle
        1600 - 1900: forward
    */
    setThrottle(ch[CH_THR]);
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
    // I2Cread(MAG_ADDRESS,0x02,1,&ST1);
    // Read magnetometer data  
    //uint8_t Mag[7];  
    //I2Cread(MAG_ADDRESS,0x03,7,Mag);    
    // Create 16 bits values from 8 bits data 
    // Magnetometer
    //int16_t mx=-(Mag[3]<<8 | Mag[2]);
    //int16_t my=-(Mag[1]<<8 | Mag[0]);
    //int16_t mz=-(Mag[5]<<8 | Mag[4]);

    printData(ax, ay, az, gx, gy,
              gz, millis(), ch[CH_STR], ch[CH_THR]);
  }
}


void convertTHR(int ch_data, int  _thrData[] ) {
  int thr;
  int DIR;
  thr = ch_data;
  //map the channel data to throttle data

  if (ch_data > 1115 && ch_data < 1520) { //reverse
    thr = map(ch_data, 1115, 1520, 255, 0 );
    DIR = LOW;
  } else if (ch_data > 1550 && ch_data < 1940) { //forward
    thr = map(ch_data, 1551, 1940, 0, 255  );
    DIR = HIGH;
  }
  else {
    thr = 0; //stop
    DIR = LOW;
  }
  _thrData[THR_THR] = thr;
  _thrData[THR_DIR] = DIR;
}

void setThrottle(int ch_data) {
  int thr;
  int DIR;
  thr = ch_data;
  //map the channel data to throttle data

  if (ch_data > 1000 && ch_data < 1520) { //reverse
    thr = map(ch_data, 1000, 1520, 255, 0 );
    DIR = LOW;
  } else if (ch_data > 1550 && ch_data < 2000) { //forward
    thr = map(ch_data, 1551, 2000, 0, 255  );
    DIR = HIGH;
  }
  else {
    thr = 0; //stop
    DIR = LOW;
  }

  //shoot through protection
  if ( DIR != PREV_DIR) {
    delay(SHOOT_DELAY);
  }
  PREV_DIR = DIR;

  digitalWrite(PIN_M1_DIR, DIR);
  digitalWrite(PIN_M2_DIR, DIR);
  SoftPWMServoPWMWrite(PIN_M1_PWM, thr); //these aren't servos use pwm
  SoftPWMServoPWMWrite(PIN_M2_PWM, thr);//these aren't servos use pwm
  if (DEBUG_SERIAL) {
    Serial.printf("thr: ch: %d, dir: %d, pwm: %d\n ", ch_data, DIR, thr);
  }
  //delay(25);
}

void setSteering(int ch_data) {
  int pos = ch_data;
  //map the channel data to steering data
  /*
     ch[1]_str:
     left: 1120
     center: 1523
     right: 1933

     car_str:
     left: 1300: 1400
     center:  1500
     right: 1582: 1633
  */

  //TODO: Record the value written to the servo: should go into global data struct
  SoftPWMServoServoWrite(PIN_STR, pos);
  if (DEBUG_SERIAL) {
    Serial.printf("str: ch: %d servo: %d\n", ch_data, pos);
  }
  //delay(25);
}


/*
   Automatic Throttle: wheels go same speed
*/
void autoThrottle(int DIR, int thr) {

  //shoot through protection
  if ( DIR != PREV_DIR) {
    delay(SHOOT_DELAY);
  }
  PREV_DIR = DIR;

  digitalWrite(PIN_M1_DIR, DIR);
  digitalWrite(PIN_M2_DIR, DIR);
  SoftPWMServoPWMWrite(PIN_M1_PWM, thr); //these aren't servos use pwm
  SoftPWMServoPWMWrite(PIN_M2_PWM, thr);//these aren't servos use pwm
  if (DEBUG_SERIAL) {
    Serial.printf("thr: dir: %d, pwm: %d\n", DIR, thr);
  }
  delay(25);
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
  int auton;
  int str;
  int thr;
  unsigned int time;



  byte size = Serial.readBytes(cmdBuf, MAX_CMD_BUF);
  cmdBuf[size] = 0;
  char* command = strtok(cmdBuf, ",");
  while (command != 0) {
    switch (cmd_cnt) {
      case CMD_AUTO:
        auton = atoi(command);
        break;
      case CMD_STR:
        str = atoi(command);
        if (DEBUG_SERIAL) {
          Serial.printf("%d, %d\n", cmd_cnt, str);
        }
        break;
      case CMD_THR:
         thr = atoi(command);
         break;
      case CMD_TIME:
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
        Serial.printf("str: %d, dir: %d, thr: %d, time: %lu\n", str, thr, time);
      }
      //do commands
      setSteering(str);
      setThrottle(thr);
    }
  }

  //delay(100);
  if (DEBUG_SERIAL) {
    Serial.printf("DONE COMMANDS: %lu\n", millis());
  }
}

/*
   printIMU to serial port
*/
void printData(float ax, float ay, float az, float gx, float gy, float gz,
               unsigned long time, int str, int thr) {
  // Serial.printf("%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%lu,%d,%d\n",
  //              ax, ay, az, gx, gy, gz, millis(), str, thr);


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


void setup() {
  Wire.begin();
  Serial.begin(9600);
  pinMode(PIN_LED1, OUTPUT);
  pinMode(PIN_M1_DIR, OUTPUT); // Motor1 DIR PIN
  pinMode(PIN_M2_DIR, OUTPUT); //Motor2 DIR PIN
  pinMode(PIN_M1_PWM, OUTPUT); // Motor1 PWM PIN
  pinMode(PIN_M2_PWM, OUTPUT); //Motor2 PWM PIN
  pinMode(PIN_KILL, OUTPUT);
  digitalWrite(PIN_LED1, LOW);
  digitalWrite(PIN_KILL, LOW);
  digitalWrite(PIN_M1_DIR, LOW);
  digitalWrite(PIN_M2_DIR, LOW);
  last_serial_time = millis();
  SoftPWMServoPWMWrite(PIN_M1_PWM, 0);
  SoftPWMServoPWMWrite(PIN_M2_PWM, 0);

  initIMU();
  for (int ii = 0; ii < 10; ii++) {
    digitalWrite(PIN_LED1, ii % 2);
    delay(200);
  }
  digitalWrite(PIN_LED1, LOW);

  for(int i=0; i<10; ++i){
    steer_history[i]=1477;
  }
  steer_next_ind=0;


  //Initialize the RC Controller data
  getRCInfo();
}

void loop() {
  doAction();
}

//Function: get The RC Control infomration
void getRCInfo() {
  //just read the channels without labels
  ch[0] = pulseIn(A1, HIGH, 25000); // Read the pulse width of
  ch[1] = pulseIn(A2, HIGH, 25000); // each channel
  ch[2] = pulseIn(A3, HIGH, 25000);
  ch[3] = pulseIn(A4, HIGH, 25000);
  //check for out of range or controller off
  if (ch[0] == 0 )
  {
    if (DEBUG_SERIAL) {
      Serial.printf("Out of Range or Powered Off\n");
    }
    //  digitalWrite(PIN_LED1, BLINK);
    //  BLINK = !BLINK;
  }
  else
  {
    for (int ii = 0; ii < channels; ii++)
    {
      if (ch[ii] > chmax[ii]) {
        chmax[ii] = ch[ii];
      }
      if (ch[ii] < chmin[ii]) {
        chmin[ii] = ch[ii];
      }
      chmid[ii] = (chmin[ii] + chmax[ii]) / 2;
      Serial.printf("Channel %d: %d, min: %d, mid: %d, max: %d\n", ii, ch[ii], chmin[ii], chmid[ii], chmax[ii]); // Print the value of
    }
  }
}

unsigned long compAvg(unsigned long *data_array, int len){
  unsigned long result=0;
  for(int i=0; i<len; ++i){
    result+=data_array[i];
  }
  return (result/len);
}
