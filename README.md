# FUBAR Labs Autonomous Racing Vehicles

Autonmous Vehicle Project at Fubar Labs for the Autonomous Powerwheels Racing compeition.
* Autonmous Powerwheels Racing event will be Makerfaire NYC 2017
* Autonmous Vehicle Competition via Sparkfun at Denver Makerfaire 2017

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

Driving model is in `current_model.py`.  Weights are on [Google Drive](goo.gl/D1WmHQ).  Line 74 of the model will have to be changed to reflect the true location/name of the weights file.

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

