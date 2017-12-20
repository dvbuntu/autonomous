#!/usr/bin/python3

# data logger for otto micro car

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
  
# -------------- Data Collector Object -------------------------------  
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
    
# -------- GPIO pin numbers for ottoMicro Car --------- 
LED_copy_to_SDcard = 2
LED_read_from_SDcard = 3
LED_autonomous = 4

button_copy_to_SDcard = 17
button_read_from_SDcard = 27
button_run_autonomous = 22

switch_power_On_Off = 10
switch_collect_data = 9

# LEDpowerStatusOfRPi = hardwired to +3.3 pin of RPi
LED_collect_data = 5
LED_power_On_Off = 6

# -------- Button/switch constants --------- 
# button push or switch position-up connects to ground, 
#  thus internal pull up  resistors are used  
ON = GPIO.LOW		# LOW signal on GPIO pin means switch is ON (up position)		
OFF = GPIO.HIGH		# HIGH signal on GPIO pin means switch is OFF (down position)
PUSHED = GPIO.LOW	# LOW signal on GPIO pin means button is PUSHED
UP = GPIO.HIGH		# HIGH signal on GPIO pin means button is UP
LED_On = GPIO.HIGH
LED_Off = GPIO.LOW

# -------------- callback functions from button/switch activity ------------------     
def callback_button_copy_to_SDcard( channel ):  
	GPIO.output( LED_copy_to_SDcard, LED_On )
	button_state = PUSHED
	while ( button_state == PUSHED ):
		button_state = GPIO.input( button_copy_to_SDcard )
	copy_data_to_SDcard()
	GPIO.output( LED_copy_to_SDcard, LED_Off )
	
def callback_button_read_from_SDcard( channel ):  
	GPIO.output( LED_read_from_SDcard, LED_On )
	button_state = PUSHED
	while ( button_state == PUSHED ):
		button_state = GPIO.input( button_read_from_SDcard )
	read_data_from_SDcard()
	GPIO.output( LED_read_from_SDcard, LED_Off )
	  
def callback_button_autonomous( channel ):  
	GPIO.output( LED_autonomous, LED_On )
	button_state = PUSHED
	while ( button_state == PUSHED ):
		button_state = GPIO.input( button_run_autonomous )
	run_in_autonomous_mode()
	GPIO.output( LED_autonomous, LED_Off )
	  
def callback_switch_power_On_Off( channel ):  
	GPIO.output( LED_power_On_Off, LED_On )
	power_On_Off_gracefully()
	
	# blink the LED as a warning to turn the switch off
	LED_state = LED_On
	while( GPIO.input( switch_power_On_Off ) == ON ):
		GPIO.output( LED_power_On_Off, LED_state )
		time.sleep( .25 )
		LED_state = LED_state ^ 1		# XOR bit 0 to turn the LED off or on
		
	GPIO.output( LED_power_On_Off, LED_Off )
		 
def callback_switch_collect_data( channel ):  
	GPIO.output( LED_collect_data, LED_On )
	collect_data() 
	
	# user pushed switch off to exit collect_data routine
	GPIO.output( LED_collect_data, LED_Off ) 

# -------- Functions called by callback functions --------- 
def copy_data_to_SDcard():
	x=1		# dummy line of code until function is defined

def read_data_from_SDcard():
	x=1		# dummy line of code until function is defined

def run_in_autonomous_mode():
	x=1		# dummy line of code until function is defined

def power_On_Off_gracefully():
	x=1		# dummy line of code until function is defined

def collect_data():
	collector=DataCollector()

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
			while( GPIO.input( switch_collect_data ) == ON ):	# wait for switch OFF to stop data collecting
				pass
	 
		camera.stop_recording()      

# ---------------- main program ------------------------------------- 
GPIO.setmode( GPIO.BCM )  
GPIO.setwarnings( False )  

#  falling edge detection setup for all buttons and switches
GPIO.setup( button_copy_to_SDcard, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( button_run_autonomous, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( button_read_from_SDcard, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( switch_power_On_Off, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( switch_collect_data, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 

GPIO.setup( LED_copy_to_SDcard, GPIO.OUT )
GPIO.setup( LED_read_from_SDcard, GPIO.OUT )
GPIO.setup( LED_autonomous, GPIO.OUT )
GPIO.setup( LED_power_On_Off, GPIO.OUT )
GPIO.setup( LED_collect_data, GPIO.OUT )

# blink LEDs as an alarm if either switch has been left in the ON (up) position
LED_state = LED_On

while(( GPIO.input( switch_power_On_Off ) == ON ) or ( GPIO.input( switch_collect_data ) == ON )):
	GPIO.output( LED_power_On_Off, LED_state )
	GPIO.output( LED_collect_data, LED_state )
	time.sleep( .25 )
	LED_state = LED_state ^ 1		# XOR bit to turn LEDs off or on
	
# turn all LED's off
GPIO.output( LED_copy_to_SDcard, LED_Off )
GPIO.output( LED_read_from_SDcard, LED_Off )
GPIO.output( LED_autonomous, LED_Off )
GPIO.output( LED_power_On_Off, LED_Off )
GPIO.output( LED_collect_data, LED_Off )
          	  
# setup callback routines for handling falling edge detection  
GPIO.add_event_detect( button_copy_to_SDcard, GPIO.FALLING, callback=callback_button_copy_to_SDcard, bouncetime=300 )  
GPIO.add_event_detect( button_run_autonomous, GPIO.FALLING, callback=callback_button_autonomous, bouncetime=300 )  
GPIO.add_event_detect( button_read_from_SDcard, GPIO.FALLING, callback=callback_button_read_from_SDcard, bouncetime=300 )  
GPIO.add_event_detect( switch_power_On_Off, GPIO.FALLING, callback=callback_switch_power_On_Off, bouncetime=300 )  
GPIO.add_event_detect( switch_collect_data, GPIO.FALLING, callback=callback_switch_collect_data, bouncetime=300 ) 
 
# input("Press Enter when ready\n>")  
    
while ( True ):
	x=1		# dummy line of code for while loop
	
GPIO.cleanup()       # clean up GPIO on CTRL+C exit  
GPIO.cleanup()       # clean up GPIO on normal exit  
