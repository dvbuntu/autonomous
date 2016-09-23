import os
import math
import numpy as np
import h5py
import glob
import scipy
import scipy.misc

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
import sklearn.metrics as metrics

import datetime
import time

from PIL import Image, ImageDraw
import pygame
import pygame.camera
from pygame.locals import *
pygame.init()
#pygame.camera.init()

debug = False
video = False

# setup model
print("setting up model")
ndata = 0
imgsize = 64
# frame size
nrows = 64
ncols = 64
wr = 0.00001
dp = 0.

# speed, accel, distance, angle
real_in = Input(shape=(2,), name='real_input')

# video frame in, grayscale
frame_in = Input(shape=(3,nrows,ncols), name='img_input')

# convolution for image input
conv1 = Convolution2D(6,3,3,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform')
conv_l1 = conv1(frame_in)
Econv_l1 = ELU()(conv_l1)
pool_l1 = MaxPooling2D(pool_size=(2,2))(Econv_l1)

conv2 = Convolution2D(8,3,3,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform')
conv_l2 = conv2(pool_l1)
Econv_l2 = ELU()(conv_l2)
pool_l2 = MaxPooling2D(pool_size=(2,2))(Econv_l2)
drop_l2 = Dropout(dp)(pool_l2)

conv3 = Convolution2D(16,3,3,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform')
conv_l3 = conv3(drop_l2)
Econv_l3 = ELU()(conv_l3)
pool_l3 = MaxPooling2D(pool_size=(2,2))(Econv_l3)
drop_l3 = Dropout(dp)(pool_l3)

flat = Flatten()(drop_l3)

M = merge([flat,real_in], mode='concat', concat_axis=1)

D1 = Dense(32,W_regularizer=l1(wr), init='lecun_uniform')(M)
ED1 = ELU()(D1)
DED1 = Dropout(dp)(ED1)

S1 = Dense(64,W_regularizer=l1(wr), init='lecun_uniform')(DED1)
ES1 = ELU()(S1)

Steer_out = Dense(1, activation='linear', name='steer_out', init='lecun_uniform')(ES1)

model = Model(input=[real_in, frame_in], output=[Steer_out])

adam = Adam(lr=0.001)


model.compile(loss=['mse'],
              optimizer=adam,
              metrics=['mse'])


# load model weights
model.load_weights('/home/ubuntu/proj/autonomous/steer_only_current.h5')

# initialize webcam
print('initialize webcame')
#cams = pygame.camera.list_cameras()
#cam = pygame.camera.Camera(cams[0],(64,64),'RGB')
#cam.start()

# make serial connection
print('connect to serial port')
if not debug:
    ser = serial.Serial('/dev/tty.usbmodem1411')
else:
    ser = open('/home/ubuntu/proj/autonomous/test_data.csv')

# initialize speeds
speeds = np.zeros(3,dtype=np.float32)

# Start the loop
start = datetime.datetime.now()
t = 0

# function for output string
def drive_str(steer, direction=1, speed=255, ms=0):
    '''Generate string to drive car to send over serial connection
    Format is:
    Steering (0-255 is L/R), Direction (0/1 for rev/forwar), Speed (0 brake, 255 full throttle), time in ms
    Str will look like:
    127,1,255,123
    '''
    return '{0},{1},{2},{3}'.format(int(steer),int(direction),int(speed),int(ms))

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
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    #plt.ion()
    figure = plt.figure()
    imageplot = plt.imshow(np.zeros((64, 64, 3), dtype=np.uint8))
    from itertools import cycle
    loop = cycle(range(10))
else:
    imageplot = False

def do_loop(i=0):
    global speeds
    global t
    # get image as numpy array
    img = pygame.surfarray.array3d(cam.get_image())
    # throw away non-square sides (left and rightmost 20 cols)
    img = img[20:-20]
    # Shrink to 64x64
    img = scipy.misc.imresize(img,(64,64),'cubic','RGB').transpose(2,1,0)
    if not debug:
        # Read acceleration information (and time, TODO)
        d = ser.readlines()
        # most recent line
        line = d[-1].strip()
    else:
        d = ser.readline()
        line = d.strip()
    # parse into list
    data = list(map(float,line.split(',')))
    # save some info
    print('Saw {0}'.format(data), end='')
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
    # create str
    s = drive_str(steer_p,ms=t)
    print(' send {0}'.format(s))
    if not debug:
        ser.write(s)
    if video == True:
        im = Image.fromarray(np.array(img.transpose(1,2,0),dtype=np.uint8))
        p = get_point(1-pred[0])
        draw = ImageDraw.Draw(im)
        draw.line((32,63, p,p),
                    fill=(255,0,0,128))
        imageplot.set_array(im)
    #if i % 10 == 0:
    #    print(i)
    return imageplot,


print('big rocket go now')
if video == True:
    animate = animation.FuncAnimation(figure, do_loop, frames=loop, interval=25, blit=False)
    print('started animation')
    plt.show()
    print('should show animation')
else:
    while True:
        do_loop()
# cleanup
ser.close()
cam.stop()
