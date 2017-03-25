# FUBAR Labs Autonomous PowerWheels Racing

Simple model in `basic_model.py`.  Currently linear with mean squared error loss (summed over outputs?)

## Inputs

* Webcam image
* Current Accel
* Current Speed
* Current Distance from rangefinder
* Current Steering wheel angle

## Outputs

* Accel (maybe braking too)
* Steering Wheel angle

# Data sources

* [DeepDrive](http://deepdrive.io)
  * [Compressed subset of DeepDrive](https://drive.google.com/open?id=0B0zbVEese408WjYtWGdJWTF0Rjg)

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

