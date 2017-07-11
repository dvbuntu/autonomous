import os
import math
import numpy as np
import h5py
import glob
import scipy
import scipy.misc
import random
import logging

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
from keras.regularizers import l2, activity_l2, l1
from keras.utils.np_utils import to_categorical
from keras import backend as K
import tflearn.metrics as metrics

import datetime
import time

cnt = 0

from PIL import Image, ImageDraw
import pygame
import pygame.camera
from pygame.locals import *
pygame.init()
pygame.camera.init()

# backup condition
def backup1(s):
    backup = 35
    if cnt % backup == backup-4:
        s = ','.join(list(map(str,[255,0,100,888888])))
    elif cnt % backup == backup -3:
        s = ','.join(list(map(str,[255,0,100,888888])))
    elif cnt % backup == backup-2:
        s = ','.join(list(map(str,[10,1,1,888888])))
    elif cnt % backup == backup-1:
        s = ','.join(list(map(str,[10,1,55,888888])))
    return s

def backup2():
    return ','.join(list(map(str,[255,0,100,888888])))

# setup model
print("setting up model")
logger.info('setting up model')
from current_model import model
adam = Adam(lr=0.001)
model.compile(loss=['mse'],
              optimizer=adam,
              metrics=['mse'])


# load model weights
model.load_weights('/home/ubuntu/proj/autonomous/steer_only_current.h5')

# initialize webcam
print('initialize webcam')
logger.info('initialize webcam')
cams = pygame.camera.list_cameras()
cam = pygame.camera.Camera(cams[0],(64,64),'RGB')
cam.start()

# make serial connection
print('connect to serial port')
logger.info('making serial connection')
if not debug:
    try:
        ser = serial.Serial('/dev/ttyACM0')
    except serial.SerialException:
        print('can not connect to serial port')
    ser.writeTimeout = 3
else:
    ser = open('/home/ubuntu/proj/autonomous/test_data.csv')

# initialize speeds
speeds = np.zeros(3,dtype=np.float32)

# Start the loop
start = datetime.datetime.now()
t = 0

# function for output string
def drive_str(steer, direction=1, speed=65, ms=0):
    '''Generate string to drive car to send over serial connection
    Format is:
    Steering (0-255 is L/R), Direction (0/1 for rev/forwar), Speed (0 brake, 255 full throttle), time in ms
    Str will look like:
    127,1,255,123
    '''
    return '{0},{1},{2},{3}\n'.format(int(steer),int(direction),int(speed),int(ms))

def get_point(s,start=0,end=63,height= 16):
    ''' Figure out the other point for animation'''
    X = int(s*(end-start))
    if X < start:
        X = start
    if X > end:
        X = end
    return (X,height)

if video == True:
    print('setup animation')
    logger.info('Setup Animation')
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    #plt.ion()
    figure = plt.figure()
    imageplot = plt.imshow(np.zeros((64, 64, 3), dtype=np.uint8))
    #loop = cycle(range(10))
else:
    imageplot = False

def do_loop(i=0):
    global speeds
    global t
    global ser
    global cnt
# get image as numpy array
    img = pygame.surfarray.array3d(cam.get_image())
    # throw away non-square sides (left and rightmost 20 cols)
    img = img[20:-20]
    # Shrink to 64x64
    img = scipy.misc.imresize(img,(64,64),'cubic','RGB').transpose(2,1,0)
    if not debug:
        # Read acceleration information (and time, TODO)
        d = ser.readline()
        # most recent line
        try:
            data = list(map(float,str(d,'ascii').split(',')))
        except ValueError:
            data = [0.01,0.01,1.0, 0.01,0.01, 0.01, 999999]
    else:
        d = ser.readline()
        line = d.strip()
        data = list(map(float,line.split(',')))
    # parse into list
    # save some info
    print('Saw {0}'.format(data), end='')
    logger.info('Saw {0}'.format(data))
    # get time in ms
    now = datetime.datetime.now()
    t_old = t
    t = int((now-start).total_seconds()*1000)
    accel = np.array(data[:3],dtype=np.float32)
    accel[2] -= 1 # subtract accel due to gravity, maybe the car can fly :p
    # rescale inputs ( decide on max speed and accel of vehicle), clamp values to these
    accel = accel / 10.
    # update speeds, accel is scaled to be m/s**2 at this point
    # so just multiply by seconds elapsed
    speeds = speeds + accel*(t-t_old)/1000.
    # now shift the accel
    accel += 0.5
    # compute magnitude of speed and accel
    mspeed = np.sqrt(np.sum(speeds*speeds))
    maccel = np.sqrt(np.sum(accel*accel))
    # make prediction
    pred = model.predict([np.array([[mspeed,maccel]]),np.array([img])])
    # clamp values
    pred[0] = np.max([np.min([pred[0],1.0]),0.])
    # rescale output steering
    steer_p = int(255-255*pred[0])
    # temporary
    #steer_p = np.clip(steer_p, 96, 160)
    # create str
    s = drive_str(steer_p,ms=t)
    #if mspeed < 0.1:
    #    s = backup2()
    #    print('back the fun bus up')
    if failsafe:
        s = backup1(s)
    print(' send {0}'.format(s))
    logger.info(' send {0}'.format(s))
    if not debug:
        try:
            ser.write(s.encode('ascii'))
        except:
            print("Couldn't write, moving on")
            logger.info('Couldn't write to serial port, skipping')
    if video == True:
        im = Image.fromarray(np.array(img.transpose(1,2,0),dtype=np.uint8))
        p = get_point(1-pred[0])
        draw = ImageDraw.Draw(im)
        draw.line((32,63, p,p),
                    fill=(255,0,0,128))
        imageplot.set_array(im)
    #if i % 10 == 0:
    #    print(i)
    time.sleep(1)
    cnt += 1
    return imageplot,


print('big rocket go now')
if video == True:
    animate = animation.FuncAnimation(figure, do_loop, interval=25,blit=False)
    print('started animation')
    plt.show()
    print('should show animation')
else:
    while True:
        do_loop()
# cleanup
ser.close()
cam.stop()
