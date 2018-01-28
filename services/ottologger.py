#!/usr/bin/python3
import sys
import time
import datetime
import picamera
import picamera.array
import numpy as np
import serial
import argparse
import RPi.GPIO as GPIO

time_format='%Y-%m-%d_%H-%M-%S'
parser=argparse.ArgumentParser(description='Records camera data from the PiCamera, along with RC command data and IMU data')
parser.add_argument('-n', '--num_frames', action='store', default=100, help='specify the number of frames per data file')
parser.add_argument('-d', '--debug', action='store_true', default=False, help='displays video on screen while recording')
#original collect script had a log flag to set up a log file, could implement
args=parser.parse_args()
num_frames=int(args.num_frames)
debug=args.debug

#Opens serial port to the arduino:
try:
  ser=serial.Serial('/dev/ttyACM0')
except serial.SerialException:
  print('Cannot connect to serial port')

#setup gpio pin stuff: we want a pin to watch for switch toggle, and to turn on an led
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN)
GPIO.setup(4, GPIO.OUT)

class DataCollector(object):
  '''this object is passed to the camera.start_recording function, which will treat it as a 
      writable object, like a stream or a file'''
  def __init__(self):
    self.imgs=np.zeros((num_frames, 64, 64, 3), dtype=np.uint8) #we put the images in here
    self.IMUdata=np.zeros((num_frames, 7), dtype=np.float32) #we put the imu data in here
    self.RCcommands=np.zeros((num_frames, 2), dtype=np.float16) #we put the RC data in here
    self.idx=0 # this is the variable to keep track of number of frames per datafile
    nowtime=datetime.datetime.now()
    self.img_file='/home/pi/autonomous/data/imgs_{0}'.format(nowtime.strftime(time_format))
    self.IMUdata_file='/home/pi/autonomous/data/IMU_{0}'.format(nowtime.strftime(time_format))
    self.RCcommands_file='/home/pi/autonomous/data/commands_{0}'.format(nowtime.strftime(time_format))
  
  def write(self, s):
    '''this is the function that is called every time the PiCamera has a new frame'''
    imdata=np.reshape(np.fromstring(s, dtype=np.uint8), (64, 64, 3), 'C')
    #now we read from the serial port and format and save the data:
    try:
      ser.flushInput()
      datainput=ser.readline()
      data=list(map(float,str(datainput,'ascii').split(','))) #formats line of data into array
      print(data)
      print("got cereal\n")

    except ValueError as err:
      print(err)
      return 
    #Note: the data from the IMU requires some processing which does not happen here:
    self.imgs[self.idx]=imdata
    accelData=np.array([data[0], data[1], data[2]], dtype=np.float32)
    gyroData=np.array([data[3], data[4], data[5]], )
    datatime=np.array([int(data[6])], dtype=np.float32)
    steer_command=int(data[7])
    gas_command=int(data[8])
    self.IMUdata[self.idx]=np.concatenate((accelData, gyroData, datatime))
    self.RCcommands[self.idx]=np.array([steer_command, gas_command])
    self.idx+=1
    if self.idx == num_frames: #default value is 100, unless user specifies otherwise
      self.idx=0
      self.flush()  
  
  def flush(self):
    '''this function is called every time the PiCamera stops recording'''
    np.savez(self.img_file, self.imgs)
    np.savez(self.IMUdata_file, self.IMUdata)
    np.savez(self.RCcommands_file, self.RCcommands)
    #this new image file name is for the next chunk of data, which starts recording now
    nowtime=datetime.datetime.now()
    self.img_file='/home/pi/autonomous/data/imgs_{0}'.format(nowtime.strftime(time_format))
    self.IMUdata_file='/home/pi/autonomous/data/IMU_{0}'.format(nowtime.strftime(time_format))
    self.RCcommands_file='/home/pi/autonomous/data/commands_{0}'.format(nowtime.strftime(time_format))
    self.imgs[:]=0
    self.IMUdata[:]=0
    self.RCcommands[:]=0


try:
  while True:
    if not GPIO.input(17):
      GPIO.wait_for_edge(17, GPIO.RISING)
    else:
      GPIO.output(4, GPIO.HIGH)

    collector=DataCollector()
    GPIO.output(4, GPIO.HIGH)
    with picamera.PiCamera() as camera:
      #Note: these are just parameters to set up the camera, so the order is not important
      camera.resolution=(64, 64) #final image size
      camera.zoom=(.125, 0, .875, 1) #crop so aspect ratio is 1:1
      camera.framerate=10 #<---- framerate (fps) determines speed of data recording
      camera.start_recording(collector, format='rgb')
      if debug:
        camera.start_preview() #displays video while it's being recorded
        input('Press enter to stop recording') # will cause hang waiting for user input
      else : #we are not in debug mode, assume data collection is happening
        GPIO.wait_for_edge(17, GPIO.FALLING) #waits until falling edge is observed from toggle
      camera.stop_recording()
      GPIO.output(4, GPIO.LOW)

except:
  camera.stop_recording()
  print("Unexpected error!: ", sys.exc_info()[0])

finally:
  GPIO.output(4, GPIO.LOW)
  ser.close()
  GPIO.cleanup()
