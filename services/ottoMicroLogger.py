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

#	CONSTANTS are in ALL CAPS

# -------- GPIO pin numbers for ottoMicro Car --------- 
LED_copy_to_SDcard = 2
LED_read_from_SDcard = 3
LED_autonomous = 4

BUTTON_copy_to_SDcard = 17
BUTTON_read_from_SDcard = 27
BUTTON_run_autonomous = 22

SWITCH_shutdown_RPi = 10
SWITCH_collect_data = 9

# LEDpowerStatusOfRPi = hardwired to +3.3 volt pin #1 of RPi
LED_collect_data = 5
LED_shutdown_RPi = 6

# -------- Button or switch (gadgets) constants --------- 
# button push or switch position-up connects to ground, 
#  thus internal pull up  resistors are used  
ON = GPIO.LOW		# LOW signal on GPIO pin means switch is ON (up position)		
OFF = GPIO.HIGH		# HIGH signal on GPIO pin means switch is OFF (down position)
PUSHED = GPIO.LOW	# LOW signal on GPIO pin means button is PUSHED
UP = GPIO.HIGH		# HIGH signal on GPIO pin means button is UP

# -------- LED state constants --------- 
LED_ON = GPIO.HIGH
LED_OFF = GPIO.LOW

# -------- Kind of error constants --------- 
NONE = 0
WARNING = 1
FATAL = 2

# -------- global variables start with a little "g" --------- 
gErrorType = NONE
gShutItDown = False

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

		except:
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



# -------- Switch / Button use cheatsheet --------- 
#
# Switch / Button		STATE		MEANING
# --------------------------------------------------------------
# SWITCH_collect_data		OFF (down)	Stop collection data if doing that		
#				ON (up)		Start collecting data
#
# SWITCH_shutdown_RPi		OFF (down)	Not in use, Normal operation		
#				ON (up)		Gracefully shutdown RPi
#
# BUTTON_copy_to_SDcard		pushed		Copy collected data to SD card
#				up		Not in use
#
# BUTTON_read_from_SDcard	pushed		Read training data to from card
#				up		Not in use
#
# BUTTON_run_autonomous		pushed		Put car in autonomous mode
#				up		Not in use
#

# -------- LED status cheatsheet --------- 
#
# LED				STATE		MEANING
# --------------------------------------------------------------
# LED_copy_to_SDcard		OFF		Not in use		
#				ON		Copy in progress
#				BLINKING	Error during copy
#
# LED_read_from_SDcard		OFF		Not in use		
#				ON		Copy in progress
#				BLINKING	Error during read
#
# LED_autonomous		OFF		Not in use		
#				ON		Car running autonomously
#				BLINKING	Autonomous error
#
# LED_collect_data		OFF		Not in use		
#				ON		Data collection in progress
#				BLINKING	Error during data collection
#
# LED_shutdown_RPi		OFF		Not in use		
#				ON		System A-OK
#				BLINKING	Tried to shut down without copying collected data to SD card
#
# LED_collect_data		both BLINKING	One or both switches not in off position on startup
# LED_shutdown_RPi
#
# LEDpowerStatusOfRPi		OFF		No power to RPi		
#				ON		RPi has +3.3 volts on pin #1



def turn_ON_LED( which_LED ):
	GPIO.output( which_LED, LED_ON )

def turn_OFF_LED( which_LED ):
	GPIO.output( which_LED, LED_OFF )

def turn_OFF_ALL_LEDs( ):
	turn_OFF_LED( LED_copy_to_SDcard )
	turn_OFF_LED( LED_read_from_SDcard )
	turn_OFF_LED( LED_autonomous )
	turn_OFF_LED( LED_shutdown_RPi )
	turn_OFF_LED( LED_collect_data )
		

# -------- Handler for clearing all gadget errors --------- 
# 	A gadget is a button or a switch. An LED is not a gadget!
def handle_gadget_exception( which_gadget, which_LED ):

	global gErrorType
	
	if( gErrorType == FATAL ):
		blinkSpeed = .01
		button_down_count = 6
	
	else:
		blinkSpeed = .2
		button_down_count = 3
			
	LED_state = LED_ON
	# blink the LED until the user holds down the button for 3 seconds
	error_not_cleared = True	
	while( error_not_cleared ):	
		if( GPIO.input( which_gadget ) == PUSHED ):
			button_down_count = button_down_count - 1
			if( button_down_count <= 0 ):
				error_not_cleared = False
				
		GPIO.output( which_LED, LED_state )	# blink the LED to show the error
		time.sleep( blinkSpeed )	
		LED_state = LED_state ^ 1		# xor bit 0 to toggle it from 0 to 1 to 0 ...

	turn_OFF_LED( which_LED )		# show the user the error has been cleared
	
	# don't leave until user releases button	
	while True:
		time.sleep( blinkSpeed )		# executes delay at least once
		if ( GPIO.input( which_gadget ) != PUSHED): break
		

# -------- Functions called by callback functions --------- 
def callback_button_copy_to_SDcard( channel ): 

	global gErrorType

	# Contrary to the falling edge detection set up previously, sometimes an interrupt
	#	will occur on the RISING edge. These must be disregarded
	if( GPIO.input( BUTTON_copy_to_SDcard ) == PUSHED ): 
		
		try:
			turn_ON_LED( LED_copy_to_SDcard )
			button_state = PUSHED
			while ( button_state == PUSHED ):
				button_state = GPIO.input( BUTTON_copy_to_SDcard )
	
			# do the copying ....
			x = y / x	# **** FORCE AN EXCEPTION FOR DEBUGGING ONLY ****
	
			turn_OFF_LED( LED_copy_to_SDcard )
		except:
			print( "card copy to card exception" )
			
			gErrorType = WARNING	# **** THIS IS SET FOR DEBUGGING ONLY ****
			
			handle_gadget_exception( BUTTON_copy_to_SDcard, LED_copy_to_SDcard )

# ------------------------------------------------- 
def callback_button_read_from_SDcard( channel ): 

	global gErrorType

	# Contrary to the falling edge detection set up previously, sometimes an interrupt
	#	will occur on the RISING edge. These must be disregarded
	if( GPIO.input( BUTTON_read_from_SDcard ) == PUSHED ): 
		
		try:
			turn_ON_LED( LED_read_from_SDcard )
			button_state = PUSHED
			while ( button_state == PUSHED ):
				button_state = GPIO.input( BUTTON_read_from_SDcard )
	
			# do the reading ....
			x = y / x	# **** FORCE AN EXCEPTION FOR DEBUGGING ONLY ****
	
			turn_OFF_LED( LED_read_from_SDcard )
		except:
			print( "card read from card exception" )
			
			gErrorType = FATAL	# **** THIS IS SET FOR DEBUGGING ONLY ****
			
			handle_gadget_exception( BUTTON_read_from_SDcard, LED_read_from_SDcard )

# ------------------------------------------------- 
def callback_button_autonomous( channel ):  

	global gErrorType

	# Contrary to the falling edge detection set up previously, sometimes an interrupt
	#	will occur on the RISING edge. These must be disregarded
	if( GPIO.input( BUTTON_run_autonomous ) == PUSHED ): 
		
		try:
			turn_ON_LED( LED_autonomous )
			button_state = PUSHED
			while ( button_state == PUSHED ):
				button_state = GPIO.input( BUTTON_run_autonomous )
	
			# do the autonomous ....
			x = y / x	# **** FORCE AN EXCEPTION FOR DEBUGGING ONLY ****
	
			turn_OFF_LED( LED_autonomous )
		except:
			print( "autonomous exception" )
			
			gErrorType = WARNING	# **** THIS IS SET FOR DEBUGGING ONLY ****
			
			handle_gadget_exception( BUTTON_run_autonomous, LED_autonomous )

# ------------------------------------------------- 
def callback_switch_shutdown_RPi( channel ):

	global gErrorType

	try:
		
		# do the graceful shutdown
		
		turn_OFF_LED( LED_shutdown_RPi )	# this probably is not needed
	
	except:
		print( "shutdown error" ) 
			
		gErrorType = FATAL	# **** THIS IS SET FOR DEBUGGING ONLY ****
			
		handle_gadget_exception( SWITCH_shutdown_RPi, LED_shutdown_RPi )

# ------------------------------------------------- 
def callback_switch_collect_data( channel ):  

	global gErrorType

	try:
		turn_ON_LED( LED_collect_data )
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
				while( GPIO.input( SWITCH_collect_data ) == ON ):	# wait for switch OFF to stop data collecting
					pass
	 
		camera.stop_recording()     
		turn_OFF_LED( LED_collect_data )
	
	except:
		print( "data collection error" ) 
			
		gErrorType = FATAL	# **** THIS IS SET FOR DEBUGGING ONLY ****
			
		handle_gadget_exception( SWITCH_collect_data, LED_collect_data )
		
# ---------------- main program ------------------------------------- 
GPIO.setmode( GPIO.BCM )  
GPIO.setwarnings( False )  

#  falling edge detection setup for all buttons and switches
GPIO.setup( BUTTON_copy_to_SDcard, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( BUTTON_run_autonomous, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( BUTTON_read_from_SDcard, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( SWITCH_shutdown_RPi, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( SWITCH_collect_data, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 

GPIO.setup( LED_copy_to_SDcard, GPIO.OUT )
GPIO.setup( LED_read_from_SDcard, GPIO.OUT )
GPIO.setup( LED_autonomous, GPIO.OUT )
GPIO.setup( LED_shutdown_RPi, GPIO.OUT )
GPIO.setup( LED_collect_data, GPIO.OUT )

# blink LEDs as an alarm if either switch has been left in the ON (up) position
LED_state = LED_ON

while(( GPIO.input( SWITCH_shutdown_RPi ) == ON ) or ( GPIO.input( SWITCH_collect_data ) == ON )):
	GPIO.output( LED_shutdown_RPi, LED_state )
	GPIO.output( LED_collect_data, LED_state )
	time.sleep( .25 )
	LED_state = LED_state ^ 1		# XOR bit to turn LEDs off or on
	
turn_OFF_ALL_LEDs( )

# setup callback routines for handling falling edge detection  
#	NOTE: because of a RPi bug, sometimes a rising edge will also trigger these routines!
GPIO.add_event_detect( BUTTON_copy_to_SDcard, GPIO.FALLING, callback=callback_button_copy_to_SDcard, bouncetime=300 )  
GPIO.add_event_detect( BUTTON_run_autonomous, GPIO.FALLING, callback=callback_button_autonomous, bouncetime=300 )  
GPIO.add_event_detect( BUTTON_read_from_SDcard, GPIO.FALLING, callback=callback_button_read_from_SDcard, bouncetime=300 )  
GPIO.add_event_detect( SWITCH_shutdown_RPi, GPIO.FALLING, callback=callback_switch_shutdown_RPi, bouncetime=300 )  
GPIO.add_event_detect( SWITCH_collect_data, GPIO.FALLING, callback=callback_switch_collect_data, bouncetime=300 ) 

# input("Press Enter when ready\n>")  

gErrorType = NONE

while ( True ):
	pass		# dummy line of code for while loop
	
GPIO.cleanup()		# clean up GPIO on CTRL+C exit  
GPIO.cleanup()		# clean up GPIO on normal exit  
