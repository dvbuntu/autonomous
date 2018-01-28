import os
import sys
import math
import numpy as np
import h5py
import glob
import scipy
import scipy.misc
import cv2
import random
import logging
import picamera
import picamera.array
import tensorflow as tf

import argparse

parser = argparse.ArgumentParser(description='Steer Otto, the autonomous tractor.')
parser.add_argument('-d','--debug', action='store_true', default=False)
parser.add_argument('-n','--no-video', action='store_true', default=False)
parser.add_argument('-f','--failsafe', action='store_true', default=False)
parser.add_argument('-l','--log', action='store', default='otto_run.log')

args = parser.parse_args()
debug = args.debug
video = not args.no_video
failsafe = args.failsafe
logfile = args.log

# setup logfile
logger = logging.getLogger('errlog')
logger.setLevel(logging.INFO)
# create file handler which logs even debug messages
fh = logging.FileHandler(logfile)
fh.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)


import serial

import keras
from keras.models import Sequential, Model
from keras.layers.core import Dense, Dropout, Activation, Flatten, Reshape
from keras.layers import Embedding, Input, merge, ELU
from keras.layers.recurrent import SimpleRNN, LSTM
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.optimizers import SGD, Adam, RMSprop
from keras.regularizers import l2, l1
from keras.utils.np_utils import to_categorical
from keras import backend as K
import tflearn.metrics as metrics

import datetime
import time



# setup model
print("setting up model")
logger.info('setting up model')
from testmodel import model
adam = Adam(lr=0.001)
model.compile(loss=['mse'],
              optimizer=adam,
              metrics=['mse'])


# load model weights
model.load_weights('./weights/weights.h5')
model._make_predict_function()
#very important, this line makes it work, I don't know why
graph = tf.get_default_graph()


# load statistics used to normalized data:
steerstats=np.load('SteerStats.npz')['arr_0']

# initialize webcam
print('initialize webcam')
logger.info('initialize webcam')
cam = cv2.VideoCapture(0)

# make serial connection
print('connect to serial port')
logger.info('making serial connection')
if not debug:
  try:
    ser = serial.Serial('/dev/ttyACM1')
  except serial.SerialException:
    print('can not connect to serial port')
  ser.writeTimeout = 3
else:
  ser = open('/home/ubuntu/proj/autonomous/test_data.csv')

class DataProcessor(object):
  '''this object is passed to the camera.start_recording function'''
  def __init__(self):
    pass

  def write(self, s):
    '''this function gets called every time the camera has a new frame'''
    imdata=np.reshape(np.fromstring(s, dtype=np.uint8), (96, 128, 3), 'C')  
    #more magic lines that make it work:
    global graph
    with graph.as_default():
      pred=model.predict(np.expand_dims(imdata, axis=0))
      steer_command=pred[0][0]*steerstats[1]+steerstats[0] # normalize by sample mean&variance
    #now we print to the arduino: autonomous bool value, steering, speed and ms
      dataline='{0}, {1}, {2}, {3}\n'.format(1, int(steer_command), 1575, 0)
      print(dataline)
      try: 
        ser.flushInput()
        ser.write(dataline.encode('ascii'))
        print(ser.readline())
	
      except: 
        print("couldn't write, moving on") 
        logger.info('couldn\'t write to serial port, skipping')

  def flush(self):
    pass

  
try:
  Processor=DataProcessor()
  with picamera.PiCamera() as camera:
    camera.resolution=(128, 96)
    camera.framerate=2
    camera.start_recording(Processor, format='rgb')
    camera.start_preview()
    input('press enter to stop recording')
    camera.stop_recording()
    
except:
  print("Unexpected error: ", sys.exc_info()[0])
  camera.stop_recording()
  raise Exception('global exception')

finally:
    # cleanup
    ser.close()

