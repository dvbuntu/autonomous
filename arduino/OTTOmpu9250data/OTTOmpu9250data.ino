#include "quaternionFilters.h"
#include "MPU9250.h"

#define AHRS true         // Set to false for basic data read
#define SerialDebug false

MPU9250 myIMU;

void setup() {
  Wire.begin();
  // TWBR = 12;  // 400 kbit/sec I2C speed
  Serial.begin(38400);
  while (1)
  {
    if (Serial.available() > 0)
    {
      char cc = Serial.read();
      if (cc == 'h' || cc == '?' || cc == '\n' || cc == '\r') {
        Serial.println("Press 's' to start.");
      }
      else if (cc == 's') {
        break;
      }
    }
  }
  // Read the WHO_AM_I register, this is a good test of communication
  byte c = myIMU.readByte(MPU9250_ADDRESS, WHO_AM_I_MPU9250);
  Serial.print("MPU9250 "); Serial.print("I AM "); Serial.print(c, HEX);
  Serial.print(" I should be "); Serial.println(0x71, HEX);
  if (c == 0x71) // WHO_AM_I should always be 0x68
  {
    Serial.println("MPU9250 is online...");

    // Start by performing self test and reporting values
    myIMU.MPU9250SelfTest(myIMU.SelfTest);
    Serial.print("x-axis self test: acceleration trim within : ");
    Serial.print(myIMU.SelfTest[0], 1); Serial.println("% of factory value");
    Serial.print("y-axis self test: acceleration trim within : ");
    Serial.print(myIMU.SelfTest[1], 1); Serial.println("% of factory value");
    Serial.print("z-axis self test: acceleration trim within : ");
    Serial.print(myIMU.SelfTest[2], 1); Serial.println("% of factory value");
    Serial.print("x-axis self test: gyration trim within : ");
    Serial.print(myIMU.SelfTest[3], 1); Serial.println("% of factory value");
    Serial.print("y-axis self test: gyration trim within : ");
    Serial.print(myIMU.SelfTest[4], 1); Serial.println("% of factory value");
    Serial.print("z-axis self test: gyration trim within : ");
    Serial.print(myIMU.SelfTest[5], 1); Serial.println("% of factory value");

    // Calibrate gyro and accelerometers, load biases in bias registers
    myIMU.calibrateMPU9250(myIMU.gyroBias, myIMU.accelBias);

    myIMU.initMPU9250();
    // Initialize device for active mode read of acclerometer, gyroscope, and
    // temperature
    Serial.println("MPU9250 initialized for active data mode....");

    // Read the WHO_AM_I register of the magnetometer, this is a good test of
    // communication
    byte d = myIMU.readByte(AK8963_ADDRESS, WHO_AM_I_AK8963);
    Serial.print("AK8963 "); Serial.print("I AM "); Serial.print(d, HEX);
    Serial.print(" I should be "); Serial.println(0x48, HEX);

    // Get magnetometer calibration from AK8963 ROM
    myIMU.initAK8963(myIMU.magCalibration);
    // Initialize device for active mode read of magnetometer
    Serial.println("AK8963 initialized for active data mode....");
    if (SerialDebug)
    {
      //  Serial.println("Calibration values: ");
      Serial.print("X-Axis sensitivity adjustment value ");
      Serial.println(myIMU.magCalibration[0], 2);
      Serial.print("Y-Axis sensitivity adjustment value ");
      Serial.println(myIMU.magCalibration[1], 2);
      Serial.print("Z-Axis sensitivity adjustment value ");
      Serial.println(myIMU.magCalibration[2], 2);
    }
  } // if (c == 0x71)
  else
  {
    Serial.print("Could not connect to MPU9250: 0x");
    Serial.println(c, HEX);
    while (1) ; // Loop forever if communication doesn't happen
  }

}

void loop() {

  myIMU.readAccelData(myIMU.accelCount);  // Read the x/y/z adc values
  myIMU.getAres();

  // Now we'll calculate the accleration value into actual g's
  // This depends on scale being set
  myIMU.ax = (float)myIMU.accelCount[0] * myIMU.aRes; // - accelBias[0];
  myIMU.ay = (float)myIMU.accelCount[1] * myIMU.aRes; // - accelBias[1];
  myIMU.az = (float)myIMU.accelCount[2] * myIMU.aRes; // - accelBias[2];

  myIMU.readGyroData(myIMU.gyroCount);  // Read the x/y/z adc values
  myIMU.getGres();

  // Calculate the gyro value into actual degrees per second
  // This depends on scale being set
  myIMU.gx = (float)myIMU.gyroCount[0] * myIMU.gRes;
  myIMU.gy = (float)myIMU.gyroCount[1] * myIMU.gRes;
  myIMU.gz = (float)myIMU.gyroCount[2] * myIMU.gRes;

  myIMU.readMagData(myIMU.magCount);  // Read the x/y/z adc values
  myIMU.getMres();
  // User environmental x-axis correction in milliGauss, should be
  // automatically calculated
  myIMU.magbias[0] = +470.;
  // User environmental x-axis correction in milliGauss TODO axis??
  myIMU.magbias[1] = +120.;
  // User environmental x-axis correction in milliGauss
  myIMU.magbias[2] = +125.;

  // Calculate the magnetometer values in milliGauss
  // Include factory calibration per data sheet and user environmental
  // corrections
  // Get actual magnetometer value, this depends on scale being set
  myIMU.mx = (float)myIMU.magCount[0] * myIMU.mRes * myIMU.magCalibration[0] -
             myIMU.magbias[0];
  myIMU.my = (float)myIMU.magCount[1] * myIMU.mRes * myIMU.magCalibration[1] -
             myIMU.magbias[1];
  myIMU.mz = (float)myIMU.magCount[2] * myIMU.mRes * myIMU.magCalibration[2] -
             myIMU.magbias[2];


  // Must be called before updating quaternions!
  myIMU.updateTime();
  MahonyQuaternionUpdate(myIMU.ax, myIMU.ay, myIMU.az, myIMU.gx * DEG_TO_RAD,
                         myIMU.gy * DEG_TO_RAD, myIMU.gz * DEG_TO_RAD, myIMU.my,
                         myIMU.mx, myIMU.mz, myIMU.deltat);
  /*
      Serial.print("q0 = "); Serial.print(*getQ());
      Serial.print(" qx = "); Serial.print(*(getQ() + 1));
      Serial.print(" qy = "); Serial.print(*(getQ() + 2));
      Serial.print(" qz = "); Serial.println(*(getQ() + 3));
  */


  myIMU.yaw   = atan2(2.0f * (*(getQ() + 1) * *(getQ() + 2) + *getQ() *
                              *(getQ() + 3)), *getQ() * *getQ() + * (getQ() + 1) * *(getQ() + 1)
                      - * (getQ() + 2) * *(getQ() + 2) - * (getQ() + 3) * *(getQ() + 3));
  myIMU.pitch = -asin(2.0f * (*(getQ() + 1) * *(getQ() + 3) - *getQ() *
                              *(getQ() + 2)));
  myIMU.roll  = atan2(2.0f * (*getQ() * *(getQ() + 1) + * (getQ() + 2) *
                              *(getQ() + 3)), *getQ() * *getQ() - * (getQ() + 1) * *(getQ() + 1)
                      - * (getQ() + 2) * *(getQ() + 2) + * (getQ() + 3) * *(getQ() + 3));

  myIMU.pitch *= RAD_TO_DEG;
  myIMU.yaw   *= RAD_TO_DEG;
  // Declination of SparkFun Electronics (40°05'26.6"N 105°11'05.9"W) is
  //   8° 30' E  ± 0° 21' (or 8.5°) on 2016-07-19
  // - http://www.ngdc.noaa.gov/geomag-web/#declination
  myIMU.yaw   -= 8.5;
  myIMU.roll  *= RAD_TO_DEG;

  /*
     myIMU.ax, myIMU.ay  myIMU.az

  */

  Serial.printf("%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%lu\n", myIMU.ax, myIMU.ay,  myIMU.az, myIMU.yaw, myIMU.pitch, myIMU.roll, millis() );
  //Serial.printf("%.0f,%.0f,%.0f\n",  myIMU.yaw,  myIMU.pitch, myIMU.roll );


  myIMU.count = millis();
  myIMU.sumCount = 0;
  myIMU.sum = 0;

  delay(10);
}


