/*
    OTTO REmote Drive:
    Drive the oTTO Tractor with a Remote RC Controller
   by Rick Anderson (ricklon)

*/
#include <Arduino.h>
#include <SoftPWMServo.h>
#include "MPU9250.h"

#define DEBUG_SERIAL false
#define MAX_CMD_BUF  20

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
#define CMD_STR 0
#define CMD_DIR 1
#define CMD_GAS 2
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

//imu unit object
MPU9250 ottoIMU;

int thrData[2] = {0, 0};

int log_thr = 0;
int log_steer = 0;

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
    setSteering(ch[CH_STR]);
    /*
       Throttling:
        1100 - 1500: reverse
        1500 - 1600: no throttle
        1600 - 1900: forward
    */
    setThrottle(ch[CH_THR]);
  }
}

int convertSTR(int ch_data) {
  int pos;
  if (ch_data > 1100 && ch_data < 1500) { //right
    pos = map(ch_data, 1100, 1500, 1589, 1525 );
  } else if (ch_data > 1550 && ch_data < 1937) { //left
    pos = map(ch_data, 1550, 1935, 1550, 1400  );
  }
  else {
    pos = 1500; //straight range: 1500 - 1550 ch_str
  }
  return pos;
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
  delay(25);
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
  delay(25);
}

/*
   Auto Steering
*/
/*
 * TODO: Convert to receiveing microseconds
 */
void autoSteer(int str) //0 - 255
{
  int pos;
  if (str <= 127 ) //steer right
  {
    pos = map(str, 127, 0, 1510, 1589);
  }
  else if (str > 128) //steer left
  {
    pos = map(str, 129, 255, 1490, 1400);
  }
  else
  {
    pos = 1500;
  }

  //TODO: Record the value written to the servo: should go into global data struct
  SoftPWMServoServoWrite(PIN_STR, pos);
  if (DEBUG_SERIAL) {
    Serial.printf("str: ch: %d servo: %d\n", str, pos);
  }
  delay(25);
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
    }
  }

  delay(100);
  if (DEBUG_SERIAL) {
    Serial.printf("DONE COMMANDS: %lu\n", millis());
  }
}

/*
   printIMU to serial port
*/
void printData()
{
  /*
   * TODO: steering microseconds
   *       throttle microseconds
   * 
   */
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

  Serial.printf("%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%lu,%d,%d\n", ottoIMU.ax, ottoIMU.ay,  ottoIMU.az, ottoIMU.gx, ottoIMU.gy, ottoIMU.gz, millis(),
  ch[CH_STR], ch[CH_THR]);
  ottoIMU.count = millis();
  ottoIMU.sumCount = 0;
  ottoIMU.sum = 0;

  delay(10);
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

  /*
    //initIMU: if not reachable stop
    if (!initIMU()) {
      while (1) {
        Serial.println("Could not connect to MPU9250: 0x");
        delay(500);
      }
    }
  */

  //Initialize the RC Controller data
  getRCInfo();
}

void loop() {
  doAction();

  if ((millis() - last_serial_time) > 100)
  {
    printData();
    last_serial_time = millis();
  }
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
