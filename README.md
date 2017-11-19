# FUBAR Labs Autonomous Racing Vehicles

Autonmous Vehicle Project at Fubar Labs for the Autonomous Powerwheels Racing compeition.
* Autonmous Powerwheels Racing event will be Makerfaire NYC 2017
* Autonmous Vehicle Competition via Sparkfun at Denver Makerfaire 2017

## Quickstart



### Car Code
```
git clone https://github.com/fubarlabs/autonomous
cd autonomous
virtualenv auto -p python3 
source auto/bin/activate
pip install -r requirements.txt
```

### Note for Arduino
Code is installed from the Raspberry PI using PLatform IO
```python2.7
sudo pip install platformio

```
Platform IO is only Python 2.7 but it can program the Arduino. In our chase it's the Fubarion SD board.


### Fubarino SD / Arduino Code

Arduino code location: ./autonomous/arduino
```
cd arduino

```
MOTTO: Small RC Car
Collection Code: MOTTOServoDtaSampleDelay.ino

```
cd MOTTOServoDataSampleDelay
pio run -t upload
```
Full Auto Code: MOTTOFullAutoDrive.ino

```
cd MOTTOFUllAutoDrive.ino
pio run -t upload
```

OTTO: Power Wheels Autonomus
Collection Code: NewOTTOFullAutoDrive.ino
```
cd NewOTTOFUllAutoDrive.ino
pio run -t upload
```
Full Auto Code:  NewOTTOFullAutoDrive.ino
```
cd NewOTTOFUllAutoDrive.ino
pio run -t upload
```


### Training code


## More documentation at the wiki

[Autonomous Project Documenatation](https://github.com/fubarlabs/autonomous/wiki)

## Code details

Simple model in `basic_model.py`.  Currently linear with mean squared error loss (summed over outputs?)

## Inputs

* Webcam image
* Current Accel
* Current Speed

## Future Inputs
* Current Distance from rangefinder
* Current Steering wheel angle

## Outputs

* Steering Wheel angle
* Maybe speed?

# Data sources

* [DeepDrive](http://deepdrive.io)
  * [Compressed subset of DeepDrive](https://drive.google.com/open?id=0B0zbVEese408WjYtWGdJWTF0Rjg)

# Notes

Driving model is in `current_model.py`.  Weights are on [Google Drive](https://goo.gl/D1WmHQ).  Line 74 of the model will have to be changed to reflect the true location/name of the weights file.

```python
#Python Libraries
import os
import math
import numpy as np
import h5py
import glob
import scipy
import scipy.misc
import random

import argparse
```

