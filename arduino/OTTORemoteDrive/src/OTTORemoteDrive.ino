/*
    OTTO REmote Drive:
    Drive the oTTO Tractor with a Remote RC Controller
   by Rick Anderson (ricklon)

*/
#include <Arduino.h>
#include <SoftPWMServo.h>

//Setup RC Controller
const int channels = 4;

/*
   What are the channels:
   0: thr: throttle
   1: str, steering
   2: aux1: pos1: OK, pos:2 Emergency Stop
   3: aux2:
*/

int ch1; // Here's where we'll keep our channel values
int ch2;
int ch3;
int ch4;

int ch[4];
int chmin[4];
int chmid[4];
int chmax[4];

/*
   RC Controller states
    out of range or off
    kill
    enable
*/
#define ACTION 0

//Setup Motor Controller
const int PIN_M1_DIR = 2; //TODO: move off i2c
const int PIN_M2_DIR = 3;
const int PIN_M1_PWM = 4;
const int PIN_M2_PWM = 7;
const int PIN_KILL = 23;

//Setup Steering Control
const int PIN_STR = 10;

//shoot through delay
int PREV_DIR = LOW;
const int SHOOT_DELAY = 250;

void setThrottle(int ch_data) {
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
  
  //shoot through protection
  if ( DIR != PREV_DIR) {
    delay(SHOOT_DELAY);
  }
  PREV_DIR = DIR;
  
  digitalWrite(PIN_M1_DIR, DIR);
  digitalWrite(PIN_M2_DIR, DIR);
  SoftPWMServoPWMWrite(PIN_M1_PWM, thr); //these aren't servos use pwm
  SoftPWMServoPWMWrite(PIN_M2_PWM, thr);//these aren't servos use pwm
  Serial.printf("thr: ch: %d, dir: %d, pwm: %d\n ", ch_data, DIR, thr);
  delay(25);
}


void setSteering(int ch_data) {
  int pos;
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


  if (ch_data > 1100 && ch_data < 1500) { //right
    pos = map(ch_data, 1100, 1500, 1589, 1525 );
  } else if (ch_data > 1550 && ch_data < 1937) { //left
    pos = map(ch_data, 1550, 1935, 1550, 1400  );
  }
  else {
    pos = 1500; //straight range: 1500 - 1550 ch_str
  }


  SoftPWMServoServoWrite(PIN_STR, pos);
  Serial.printf("str: ch: %d servo: %d\n ", ch_data, pos);
  delay(25);
}




void doRCAction() {
  ch[0] = pulseIn(A1, HIGH, 25000); // Read the pulse width of
  ch[1] = pulseIn(A2, HIGH, 25000); // each channel
  ch[2] = pulseIn(A3, HIGH, 25000);
  ch[3] = pulseIn(A4, HIGH, 25000);

  if (ch[2] > 1500 ) {
    digitalWrite(PIN_KILL, HIGH);
    Serial.println("KILL HIGH");
  }
  else {
    digitalWrite(PIN_KILL, LOW);
  }

  if (ch[0] == 0 )
  {
    Serial.printf("Out of Range or Powered Off\n");
    //set brake
    //kill the machine
  }
  else
  {
    /*
       steering 1100 - 1500 map left
       steering between 1500 - 1600 straight
        steering 1600 - 1900 map left
    */

    setSteering(ch[0]);

    /*
       Throttling:
        1100 - 1500: reverse
        1500 - 1600: no throttle
        1600 - 1900: forward
    */

    setThrottle(ch[1]);
  }

}


void setup() {
  Serial.begin(9600);
  pinMode(PIN_M1_DIR, OUTPUT); // Motor1 DIR PIN
  pinMode(PIN_M2_DIR, OUTPUT); //Motor2 DIR PIN
  pinMode(PIN_M1_PWM, OUTPUT); // Motor1 PWM PIN
  pinMode(PIN_M2_PWM, OUTPUT); //Motor2 PWM PIN
  pinMode(PIN_KILL, OUTPUT);
  digitalWrite(PIN_KILL, LOW);
  digitalWrite(PIN_M1_DIR, LOW);
  digitalWrite(PIN_M2_DIR, LOW);
  SoftPWMServoServoWrite(PIN_M1_PWM, 0);
  SoftPWMServoServoWrite(PIN_M2_PWM, 0);

  /*
     Initialize the RC Controller data
  */
  getRCInfo();
  /*
    for (int ii = 0; ii < channels; ii++) {
    chmin[ii] = ch[ii];
    chmid[ii] = ch[ii];
    chmax[ii] = ch[ii];
    }
  */
}

void loop() {
  doRCAction();


}


int getRCAction() {
  ch[0] = pulseIn(A1, HIGH, 25000); // Read the pulse width of
  ch[1] = pulseIn(A2, HIGH, 25000); // each channel
  ch[2] = pulseIn(A3, HIGH, 25000);
  ch[3] = pulseIn(A4, HIGH, 25000);
  return ACTION;
}


//Function: get The RC Control infomration
void getRCInfo() {
  ch[0] = pulseIn(A1, HIGH, 25000); // Read the pulse width of
  ch[1] = pulseIn(A2, HIGH, 25000); // each channel
  ch[2] = pulseIn(A3, HIGH, 25000);
  ch[3] = pulseIn(A4, HIGH, 25000);
  //check for out of range or controller off
  if (ch[0] == 0 )
  {
    Serial.printf("Out of Range or Powered Off\n");
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
