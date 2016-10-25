import os
import math
import numpy as np
import glob
import scipy
import scipy.misc
import datetime
import time

import argparse


parser = argparse.ArgumentParser(description='Steer Otto, the autonomous tractor and collect data.')
parser.add_argument('-n','--num_frames', action='store', default=100)
parser.add_argument('-d','--debug', action='store_true', default=False)

args = parser.parse_args()
num_frames = args.num_frames
debug = args.debug

import serial

from PIL import Image, ImageDraw
import pygame
import pygame.camera
from pygame.locals import *
pygame.init()
pygame.camera.init()

# initialize webcam
print('initialize webcam')
cams = pygame.camera.list_cameras()
cam = pygame.camera.Camera(cams[0],(64,64),'RGB')
cam.start()

time_format = '%Y-%m-%d_%H:%M:%S'
date = datetime.datetime.now()

imgs_file = 'imgs_{0}'.format(date.strftime(time_format))
speedx_file = 'speedx_{0}'.format(date.strftime(time_format))
targets_file = 'targets_{0}'.format(date.strftime(time_format))

print('connect to serial port')
if not debug:
    ser = serial.Serial('/dev/ttyACM0')
    if(ser.isOpen() == False):
        ser.open()
else:
    ser = open('/home/ubuntu/proj/autonomous/test_collect.csv')


# setup storage
imgs = np.zeros((num_frames,3,64,64),dtype=np.uint8)
speedx = np.zeros((num_frames,2),dtype=np.float16)
targets = np.zeros((num_frames,2),dtype=np.float16)

# Drive in remote control mode
idx = 0
try:
    while(True):
        # Maybe send 'Ok, ready' to the serial port
        # take web footage (every second or whatever)
        img = pygame.surfarray.array3d(cam.get_image())
        ## throw away non-square sides (left and rightmost 20 cols)
        img = img[20:-20]
        ## Shrink to 64x64
        img = scipy.misc.imresize(img,(64,64),'cubic','RGB').transpose(2,1,0)
        # Receive steering + gas (inc. direction)
        if not debug:
            ## Read acceleration information (and time, TODO)
            d = ser.readline()
            ## most recent line
            data = list(map(int,str(d,'ascii').split(',')))
        else:
            d = ser.readline()
            line = d.strip()
            data = list(map(int,line.split(',')))
        # Record all in convenient format
        steer = data[0]
        direction = data[1]
        if direction:
            gas = data[2]
        else:
            gas = -1*data[2]
        time = data[3]
        speed = data[4]
        accel = data[5]
        # Stuff into appropriate arrays
        imgs[idx] = np.array(img,dtype=np.uint8)
        speedx[idx] = np.array([speed,accel],dtype=np.float16)
        targets[idx] = np.array([steer,gas],dtype=np.float16)
        # increment counter, maybe save
        idx += 1
        if idx % num_frames == 0:
            np.savez(imgs_file,imgs)
            np.savez(speedx_file,speedx)
            np.savez(targets_file,targets)
            ## Make new data files
            date = datetime.datetime.now()
            imgs_file = 'imgs_{0}'.format(date.strftime(time_format))
            speedx_file = 'speedx_{0}'.format(date.strftime(time_format))
            targets_file = 'targets_{0}'.format(date.strftime(time_format))
            # zero out storage
            imgs[:] = 0
            speedx[:] = 0
            targets[:] = 0
        time.sleep(1)
except:
    np.savez(imgs_file,imgs[:idx])
    np.savez(speedx_file,speedx[:idx])
    np.savez(targets_file,targets[:idx])

