import os
import sys
import math
import numpy as np
import glob
import scipy
import scipy.misc
import cv2
import datetime
import time as timemod
import logging

import argparse


parser = argparse.ArgumentParser(description='Steer Otto, the autonomous tractor and collect data.')
parser.add_argument('-n','--num_frames', action='store', default=100)
parser.add_argument('-d','--debug', action='store_true', default=False)
parser.add_argument('-l','--log', action='store', default='otto.log')

args = parser.parse_args()
num_frames = int(args.num_frames)
debug = args.debug
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

from PIL import Image, ImageDraw

# initialize webcam
print('initialize webcam')
logger.info('initialize webcam')
cam = cv2.VideoCapture(0)
timemod.sleep(3) # let camera warm up


time_format = '%Y-%m-%d_%H:%M:%S'
date = datetime.datetime.now()

imgs_file = './data/imgs_{0}'.format(date.strftime(time_format))
speedx_file = './data/speedx_{0}'.format(date.strftime(time_format))
targets_file = './data/targets_{0}'.format(date.strftime(time_format))

print('connect to serial port')
logger.info('connect to serial port')
if not debug:
    try:
        ser = serial.Serial('/dev/ttyACM0')
    except serial.SerialException:
        print('can not connect to serial port')
        logger.error('can not connect to serial port')
else:
    ser = open('./symdata/testdata.csv')

# initialize speeds
speeds = np.zeros(3,dtype=np.float32)

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
        retval, img = cam.read()

        ## throw away non-square sides (left and rightmost 20 cols)
        if retval == False:
            print("camera is not reading images")
        img = img[20:-20]
        ## Shrink to 64x64
        img = scipy.misc.imresize(img,(64,64),'cubic','RGB').transpose(2,0,1)
        # Receive steering + gas (inc. direction)
        if not debug:
                try:
                    ## Read acceleration information (and time, TODO)
                    d = ser.readline()
                    ## most recent line
                    #data = list(map(int,str(d,'ascii').split(',')))
                    #print(d, 'ascii')
                    line = d.strip()
                    data = line.split(b',')
                    data = list(map(float,str(d,'ascii').split(',')))
                except ValueError as err:
                    print(err)
                    logger.error(err)
                    continue
        else:
            d = ser.readline()
            line = d.strip()
            data = list(map(int,line.split(',')))
        # Record all in convenient format
        accel = np.array([float(data[0]),float(data[1]),float(data[2])], dtype=np.float16)
        gx = float(data[3])
        gy = float(data[4])
        gz = float(data[5])
        time = int(data[6])
        steer_raw = int(data[7])
        gas_raw = int(data[8])
        #direction = data[1]
        #if direction:
        #    gas = data[2]
        #else:
        #    gas = -1*data[2]
        #time = data[3]
        #speed = data[4]
        #accel = data[5]
        accel[2] -= 1 # subtract accel due to gravity, maybe the car can fly :p
        # rescale inputs ( decide on max speed and accel of vehicle), clamp values to these
        accel = accel / 10.
        # update speeds, accel is scaled to be m/s**2 at this point
        # so just multiply by seconds elapsed
        #speeds = speeds + accel*(t-t_old)/1000.
        # now shift the accel
        accel += 0.5
        # compute magnitude of speed and accel
        #mspeed = np.sqrt(np.sum(speeds*speeds))
        mspeed = 99
        maccel = np.sqrt(np.sum(accel*accel))

        # Stuff into appropriate arrays
        imgs[idx % num_frames] = np.array(img,dtype=np.uint8)
        speedx[idx % num_frames] = np.array([mspeed,maccel],dtype=np.float16)
        targets[idx % num_frames] = np.array([steer_raw,gas_raw],dtype=np.float16)
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
        # timemod.sleep(1) # force pause for one photo a second

except:
    np.savez(imgs_file,imgs[:idx])
    np.savez(speedx_file,speedx[:idx])
    np.savez(targets_file,targets[:idx])
    print("Unexpected error: ", sys.exc_info()[0])
    raise Exception('global exception')

finally:
    cam.release()
    print("Finally: Camera release")


