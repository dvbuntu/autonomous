/*
    RC Remote Echo:
    ECHO a Remote RC Controller
   by Rick Anderson (ricklon)

*/
#include <Arduino.h>
#include <SoftPWMServo.h>

const int PIN_KILL = 23;
const int PIN_THR = 12;
const int PIN_STR = 13;
const int PIN_AUX = 23;

#define STR 0
#define THR 1
#define KILL 2
#define AUX 3

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


void doRCAction() {
  ch[STR] = pulseIn(PIN_STR, HIGH, 25000); // Read the pulse width of
  ch[THR] = pulseIn(PIN_THR, HIGH, 25000); // each channel
  ch[KILL] = pulseIn(PIN_KILL, HIGH, 25000);
  ch[AUX] = pulseIn(PIN_AUX, HIGH, 25000);

// RC Actions
  if (ch[KILL] > 1500 ) {
    Serial.println("AUTO ON");
  }
  else {
    Serial.println("AUTO OFF");
  }

  if (ch[STR] == 0 )
  {
    Serial.printf("Out of Range or Powered Off\n");
    Serial.println("This should be the same as a kill switch");
    //set brake
    //kill the machine
  }
  else
  {
    Serial.println("COMMANDS");
  }
}

// Function: get The RC Control infomration
void getRCInfo() {
  ch[STR] = pulseIn(PIN_STR, HIGH, 25000); // Read the pulse width of
  ch[THR] = pulseIn(PIN_THR, HIGH, 25000); // each channel
  ch[KILL] = pulseIn(PIN_KILL, HIGH, 25000);
  ch[AUX] = pulseIn(PIN_AUX, HIGH, 25000);
  //check for out of range or controller off
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


void setup() {
  Serial.begin(9600);

  pinMode(PIN_STR, INPUT);
  pinMode(PIN_THR, INPUT);
  pinMode(PIN_KILL, INPUT);
  pinMode(PIN_AUX, INPUT);

  getRCInfo();

}

void loop() {
  getRCInfo();
  doRCAction();
  delay(250);
}

