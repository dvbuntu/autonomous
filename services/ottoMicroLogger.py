#!/usr/bin/python3

import sys, os

import time
import datetime
import picamera
import picamera.array
import numpy as np
import serial
import argparse
import RPi.GPIO as GPIO
import subprocess  
from subprocess import call

import logging
logging.basicConfig(filename='ottoMicroLogger.log',level=logging.DEBUG)
logging.debug( '\n new session \n' )

# for call USB stick functions
# import ottoUSBdriveFunctions as USBfunct

# -------- New Power On/Off functionality --------- 

# 1- User holds boot switch in ON position which energizes power relay coil ( power LED remains unlit )
# 2- Relay contacts close supplying 5 volts to Pi.
# 3- Pi boots, executes service program which also energizes relay coil
# 4- Pi turns on power LED to indicate to user that the Pi is under control
# 5- User releases toggle switch, but Pi has already latched relay contacts closed so it remains powered
# 6- Program continues to execute until user flips power off switch telling Pi to shut it down

#	CONSTANTS are in ALL CAPS

# -------- GPIO pin numbers for ottoMicro Car --------- 
LED_read_from_USBdrive = 2
LED_save_to_USBdrive = 3
LED_collect_data = 4
LED_autonomous = 17
LED_shutdown_RPi = 27
LED_boot_RPi = 22

SWITCH_collect_data = 10
SWITCH_save_to_USBdrive = 9
SWITCH_read_from_USBdrive = 11
SWITCH_autonomous = 5
SWITCH_shutdown_RPi = 6
# SWITCH_boot_RPi -> daughter board relay coil

OUTPUT_to_relay = 13

# -------- Switch constants --------- 
# switch position-UP connects GPIO pin to GROUND, 
#  thus internal pull up  resistors are used  
#  and LOW and HIGH signals are opposite to usual ON and OFF conventions
SWITCH_UP = GPIO.LOW		# LOW signal on GPIO pin means switch is in up position		
SWITCH_DOWN = GPIO.HIGH		# HIGH signal on GPIO pin means switch is in down position

# -------- LED state constants --------- 
LED_ON = GPIO.HIGH
LED_OFF = GPIO.LOW

# -------- Relay state constants --------- 
RELAY_ON = GPIO.HIGH
RELAY_OFF = GPIO.LOW

# -------- Kind of error constants --------- 
NONE = 0
WARNING = 1
FATAL = 2
NO_USB_DRIVE_WARNING = 3
AUTONOMOUS_WARNING = 4
RECORDED_DATA_NOT_SAVED = 5

# --------Old Data Collection Command Line Startup Code--------- 
time_format='%Y-%m-%d_%H-%M-%S'

#	**** fubarino not connected yet for debugging purposes ****
#Opens serial port to the arduino:
#try:
#	ser=serial.Serial('/dev/ttyACM0')
#except serial.SerialException:
#	logging.debug( 'gCannot connect to serial port' )
 
# -------------- Data Collector Object -------------------------------  

NUM_FRAMES = 100

class DataCollector(object):
	'''this object is passed to the camera.start_recording function, which will treat it as a 
	writable object, like a stream or a file'''
	def __init__(self):
		self.imgs=np.zeros((NUM_FRAMES, 64, 64, 3), dtype=np.uint8) #we put the images in here
		self.IMUdata=np.zeros((NUM_FRAMES, 7), dtype=np.float32) #we put the imu data in here
		self.RCcommands=np.zeros((NUM_FRAMES, 2), dtype=np.float16) #we put the RC data in here
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
			logging.debug( data )
			logging.debug( 'got cereal\n' )

		except:
			logging.debug( err )
			logging.debug( 'exception in data collection write' )
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
		if self.idx == NUM_FRAMES: #default value is 100, unless user specifies otherwise
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
# SWITCH_boot_RPi		momentary up	Boot up RPi		
#				down		normal RPi operation
#
# SWITCH_shutdown_RPi		momentary up	Gracefully shutdown RPi		
#				down		normal RPi operation
#
# SWITCH_autonomous		up		Put car in autonomous mode
#				down		normal RPi operation
#
# SWITCH_collect_data		up		Start collecting data
#				down		Stop collection data if doing that		
#
# SWITCH_save_to_USBdrive	momentary up	Copy collected data to USB drive
#				down		normal RPi operation
#
# SWITCH_read_from_USBdrive	momentary up	Read training data to from USB drive
#				down		normal RPi operation
#

# -------- LED status cheatsheet --------- 
#
# 	SLOW blink -> WARNING ERROR
#	FAST blink -> FATAL ERROR
#
# LED				STATE		MEANING
# --------------------------------------------------------------
# LED_boot_RPi			OFF		No power to RPi		
#				ON		Turned on when RPi has finished booting
#				BLINKING	Not defined yet
#
# LED_shutdown_RPi		OFF		Not in use		
#				ON		System A-OK
#				BLINKING	Tried to shut down without copying collected data to USB drive
#
# LED_autonomous		OFF		Not in use		
#				ON		Car running autonomously
#				BLINKING	Autonomous error
#
# LED_collect_data		OFF		Not in use		
#				ON		Data collection in progress
#				BLINKING	Error during data collection
#
# LED_save_to_USBdrive		OFF		Not in use		
#				ON		Copy in progress
#				BLINKING	Error during copy
#
# LED_read_from_USBdrive	OFF		Not in use		
#				ON		Copy in progress
#				BLINKING	Error during read
#

# -------- LED functions to make code clearer --------- 
def turn_ON_LED( which_LED ):
	GPIO.output( which_LED, LED_ON )

def turn_OFF_LED( which_LED ):
	GPIO.output( which_LED, LED_OFF )	
	
# -------------- Global Variables -------------------------------
# -------- note: global variables start with a little "g" --------- 

g_Wants_To_See_Video = True
g_Camera_Is_Recording = False
g_Recorded_Data_Not_Saved = False
g_No_Callback_Function_Running = True
g_Current_Exception_Not_Finished = False

# -------- Handler for clearing all switch errors --------- 
def handle_switch_exception( kind_Of_Exception, which_switch, which_LED, message ):
	global g_Current_Exception_Not_Finished
	
	if( g_Current_Exception_Not_Finished ):
		logging.debug( '*** another exception occurred' )
		
	else: 
		g_Current_Exception_Not_Finished = True
		logging.debug( message )
		logging.debug( sys.exc_info()[0] )
		
		if( kind_Of_Exception == FATAL ):
			blinkSpeed = .1 
			switch_on_count = 6
		else:	
			blinkSpeed = .2
			switch_on_count = 3
		
		LED_state = LED_ON
		# blink the LED until the user holds down the button for 3 seconds
		error_not_cleared = True	
		while( error_not_cleared ):	
			if( GPIO.input( which_switch ) == SWITCH_UP ):
				switch_on_count = switch_on_count - 1
				if( switch_on_count <= 0 ):
					error_not_cleared = False
				
			GPIO.output( which_LED, LED_state )	# blink the LED to show the error
			time.sleep( blinkSpeed )	
			LED_state = LED_state ^ 1		# xor bit 0 to toggle it from 0 to 1 to 0 ...

		turn_OFF_LED( which_LED )		# show the user the error has been cleared
	
		# don't leave until we're sure user released button	
		while True:
			time.sleep( blinkSpeed )		# executes delay at least once
			if ( GPIO.input( which_switch ) == SWITCH_DOWN ): break
	
		if( kind_Of_Exception == FATAL ):
			logging.debug( "*** FATAL exception handled" )
		else:	
			logging.debug( "*** WARNING exception handled" )
		
		g_Current_Exception_Not_Finished = False
	


# -------- Functions called by switch callback functions --------- 
def callback_switch_save_to_USBdrive( channel ): 
	global g_No_Callback_Function_Running
	
	# don't reenter an already running callback and don't respond to a high to low switch transition
	if(( g_No_Callback_Function_Running ) and ( GPIO.input( SWITCH_save_to_USBdrive ) == SWITCH_UP )): 
		g_No_Callback_Function_Running = False
			
		try:
			turn_ON_LED( LED_save_to_USBdrive )
			switch_state = SWITCH_UP
			while ( switch_state == SWITCH_UP ):
				switch_state = GPIO.input( SWITCH_save_to_USBdrive )
	
			# do the copying ....
			logging.debug( 'attempting to save Data folder to USB drive' )


			returned_Error = WARNING
			
			# 	try to unmount the USB drive if it is mounted
			#		if it isn't mounted, pipe the error message to /log.txt 
			

			p = subprocess.Popen( ['mkdir', '/mnt/usbdrive'], stdout=subprocess.PIPE, stderr=subprocess.PIPE )
			out, err = p.communicate()
			
			logging.debug( err )
			logging.debug( p.returncode )
			logging.debug( 'after mkdir' )
			
			#	decode() deals with python byte literal craziness
#			if( out.decode() == "/dev/sda1\n" ):
#				call( "cp -a ~/autonomous/data/ /media/usb1/", shell=True )
#				logging.debug( 'Data folder saved to USB drive' )
#			else:
#				returned_Error = WARNING

#			call ( "/usr/bin/mkdir /mnt/usbdrive 2> /log.txt", shell=True )
#			call ( "/usr/bin/mount /dev/sda1 /mnt/usbdrive 2> /log.txt", shell=True )


			p = subprocess.Popen( ['mount', '/dev/sda1 /mnt/usbdrive'], stdout=subprocess.PIPE, stderr=subprocess.PIPE )
			out, err = p.communicate()
			logging.debug( err )
			logging.debug( p.returncode )
			logging.debug( 'after mount' )


			call( "cp -a /test.txt /mnt/usbdrive/ 2> /home/pi/log.txt", shell=True )
			logging.debug( 'after cp' )
			
			call ( "/usr/bin/umount /dev/sda1 2> /home/pi/log.txt", shell=True )
			logging.debug( 'after umount' )
			
			logging.debug( 'Data folder saved to USB drive' )
				
			turn_OFF_LED( LED_save_to_USBdrive )
			
		except:
			
			if( returned_Error == WARNING ):			
				message = "copy to USB drive warning: USB drive not found"
				kind_Of_Exception = WARNING					
			else:			
				message = "copy to USB drive fatal error"
				kind_Of_Exception = FATAL	
			
			handle_switch_exception( kind_Of_Exception, SWITCH_save_to_USBdrive, LED_save_to_USBdrive, message )

		g_No_Callback_Function_Running = True
	else: 
		logging.debug( 'skipped: another callback from save_to_USBdrive' )
	
# ------------------------------------------------- 
def callback_switch_read_from_USBdrive( channel ):
	global g_No_Callback_Function_Running
	
	# don't reenter an already running callback and don't respond to a high to low switch transition
	if(( g_No_Callback_Function_Running ) and ( GPIO.input( SWITCH_read_from_USBdrive ) == SWITCH_UP )): 
		g_No_Callback_Function_Running = False
				
		try:
			turn_ON_LED( LED_read_from_USBdrive )
			switch_state = SWITCH_UP
			while ( switch_state == SWITCH_UP ):
				switch_state = GPIO.input( SWITCH_read_from_USBdrive )
	
			# do the reading ....
			# returned_Error = WARNING	# **** set for debugging ****
			# raise Exception( "exception for debugging purposes" )
			logging.debug( 'from read_from_USBdrive:' )
			call( "ls /media", shell=True )
			returned_Error = NONE		# **** for debugging ****
	
			turn_OFF_LED( LED_read_from_USBdrive )
			
		except:
			if( returned_Error == WARNING ):			
				message = "read from USB drive warning: USB drive not found"
				kind_Of_Exception = WARNING					
			else:			
				logging.debug( 'read error: I/O' )
				message = "read from USB drive fatal error"
				kind_Of_Exception = FATAL	
			
			handle_switch_exception( kind_Of_Exception, SWITCH_read_from_USBdrive, LED_read_from_USBdrive, message )

		g_No_Callback_Function_Running = True
	else: 
		logging.debug( 'skipped: another callback from read_from_USBdrive' )
	 
# ------------------------------------------------- 
def callback_switch_autonomous( channel ):  
	global g_No_Callback_Function_Running

	# don't reenter an already running callback and don't respond to a high to low switch transition
	if(( g_No_Callback_Function_Running ) and ( GPIO.input( SWITCH_autonomous ) == SWITCH_UP )): 
		g_No_Callback_Function_Running = False
				
		try:
			turn_ON_LED( LED_autonomous )
			switch_state = SWITCH_UP
			while ( switch_state == SWITCH_UP ):
				switch_state = GPIO.input( SWITCH_autonomous )
	
			# do the autonomous ....
			returned_Error = FATAL	# **** set for debugging ****
			raise Exception( "exception for debugging purposes" )
	
			turn_OFF_LED( LED_autonomous )
			
		except:
			if( returned_Error == WARNING ):			
				message = "autonomous error warning"
				kind_Of_Exception = WARNING					
			else:			
				message = "autonomous error fatal error"
				kind_Of_Exception = FATAL	
			
			handle_switch_exception( kind_Of_Exception, SWITCH_autonomous, LED_autonomous, message )

		g_No_Callback_Function_Running = True
	else: 
		logging.debug( 'skipped: another callback from autonomous' )
	 
# ------------------------------------------------- 
def callback_switch_collect_data( channel ):  
	global g_Recorded_Data_Not_Saved
	global g_Wants_To_See_Video
	global g_Camera_Is_Recording
	global g_No_Callback_Function_Running

	# don't reenter an already running callback and don't respond to a high to low switch transition
	if(( g_No_Callback_Function_Running ) and ( GPIO.input( SWITCH_collect_data ) == SWITCH_UP )): 
		g_No_Callback_Function_Running = False
		
		try:
			logging.debug( '* starting recording' )
			turn_ON_LED( LED_collect_data )
			
			collector=DataCollector()
			
			with picamera.PiCamera() as camera:
				#Note: these are just parameters to set up the camera, so the order is not important
				camera.resolution=(64, 64) #final image size
				camera.zoom=(.125, 0, .875, 1) #crop so aspect ratio is 1:1
				camera.framerate=10 #<---- framerate (fps) determines speed of data recording
				camera.start_recording( collector, format='rgb' )
				g_Camera_Is_Recording = True
				if ( g_Wants_To_See_Video ):
					camera.start_preview() #displays video while it's being recorded
				
				while( GPIO.input( SWITCH_collect_data ) == SWITCH_UP ):
					pass
					
				camera.stop_recording()
				g_Camera_Is_Recording = False
				turn_OFF_LED( LED_collect_data )
				time.sleep( .1 )	# wait a little just in case the switch isn't stable
				
		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			logging.debug( exc_type, fname, "   line number = ", exc_tb.tb_lineno )
			message = "* Data collection fatal error"
			kind_Of_Exception = FATAL	

			handle_switch_exception( kind_Of_Exception, SWITCH_collect_data, LED_collect_data, message )

		g_No_Callback_Function_Running = True
	else: 
		logging.debug( 'skipped: another callback from collect_data' )
		
		if( g_Camera_Is_Recording ):
			logging.debug( 'camera is still ON' )
		else:
			logging.debug( 'camera is turned OFF' )
	 
# ------------------------------------------------- 
#	regular exception handling not used with shutdown function
def callback_switch_shutdown_RPi( channel ):
	global g_Recorded_Data_Not_Saved
	global g_No_Callback_Function_Running

	# don't reenter an already running callback and don't respond to a high to low switch transition
	if(( g_No_Callback_Function_Running ) and ( GPIO.input( SWITCH_shutdown_RPi ) == SWITCH_UP )): 
		g_No_Callback_Function_Running = False
		
		blinkSpeed = .2
		switch_on_count = 15
		turn_ON_all_LEDs( )		
		LEDs_state = LED_ON
		
		g_Recorded_Data_Not_Saved = True	# debugging
		logging.debug( 'starting shutdown' )
			
		while( GPIO.input( SWITCH_shutdown_RPi ) == SWITCH_UP ):	
			if( switch_on_count > 0 ):
				time.sleep( blinkSpeed )
				
				if( g_Recorded_Data_Not_Saved ):		# blink all LEDs as warning data not saved
					LEDs_state = LEDs_state ^ 1		# xor bit 0 to toggle it from 0 to 1 to 0 ...
				
				if( LEDs_state == LED_ON ):
					turn_ON_all_LEDs()
				else:
					turn_OFF_all_LEDs()
				
				switch_on_count = switch_on_count - 1
			else:
				break
				
		if( switch_on_count <= 0 ):
			# shut down pi, data saved or not
			turn_OFF_all_LEDs()		# show the user the error has been cleared
			GPIO.output( OUTPUT_to_relay, RELAY_OFF )
			logging.debug( 'calling pi shutdown' )
			call( "sudo shutdown now", shell=True )
		
		#	user changed his mind, exit function without shut down
		turn_OFF_all_LEDs()		# show the user the shutdown has been stopped
		turn_ON_LED( LED_boot_RPi )	# turn this one back on to show power is still on
		logging.debug( 'user changed mind about shutdown' )
		g_No_Callback_Function_Running = True
		
	else: 
		logging.debug( 'skipped: another callback from shutdown_RPi' )
				 	
# ------------------------------------------------- 
def turn_OFF_all_LEDs():
	turn_OFF_LED( LED_save_to_USBdrive )
	turn_OFF_LED( LED_read_from_USBdrive )
	turn_OFF_LED( LED_collect_data )
	turn_OFF_LED( LED_shutdown_RPi )
	turn_OFF_LED( LED_autonomous )
	turn_OFF_LED( LED_boot_RPi )
	 	
# ------------------------------------------------- 
def turn_ON_all_LEDs():
	turn_ON_LED( LED_save_to_USBdrive )
	turn_ON_LED( LED_read_from_USBdrive )
	turn_ON_LED( LED_collect_data )
	turn_ON_LED( LED_shutdown_RPi )
	turn_ON_LED( LED_autonomous )
	turn_ON_LED( LED_boot_RPi )
	 	
# ------------------------------------------------- 
def initialize_RPi_Stuff():
	
	# blink LEDs as an alarm if autonmous or collect switches have been left up
	LED_state = LED_ON

	while( GPIO.input( SWITCH_collect_data ) == SWITCH_UP ):
		GPIO.output( LED_collect_data, LED_state )
		time.sleep( .25 )
		LED_state = LED_state ^ 1		# XOR bit to turn LEDs off or on
		
	while( GPIO.input( SWITCH_autonomous ) == SWITCH_UP ): 
		GPIO.output( LED_autonomous, LED_state )
		time.sleep( .25 )
		LED_state = LED_state ^ 1		# XOR bit to turn LEDs off or on
	
	# turn off all LEDs for initialization
	turn_OFF_all_LEDs()

# ---------------- MAIN PROGRAM ------------------------------------- 

GPIO.setmode( GPIO.BCM )  
GPIO.setwarnings( False )

#  falling edge detection setup for all switchs 
GPIO.setup( SWITCH_save_to_USBdrive, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( SWITCH_autonomous, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( SWITCH_read_from_USBdrive, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( SWITCH_shutdown_RPi, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( SWITCH_collect_data, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 

GPIO.setup( LED_read_from_USBdrive, GPIO.OUT )
GPIO.setup( LED_save_to_USBdrive, GPIO.OUT )
GPIO.setup( LED_collect_data, GPIO.OUT )
GPIO.setup( LED_shutdown_RPi, GPIO.OUT )
GPIO.setup( LED_autonomous, GPIO.OUT )
GPIO.setup( LED_boot_RPi, GPIO.OUT )

GPIO.setup( OUTPUT_to_relay, GPIO.OUT )

# setup callback routines for switch falling edge detection  
#	NOTE: because of a RPi bug, sometimes a rising edge will also trigger these routines!
GPIO.add_event_detect( SWITCH_save_to_USBdrive, GPIO.FALLING, callback=callback_switch_save_to_USBdrive, bouncetime=50 )  
GPIO.add_event_detect( SWITCH_autonomous, GPIO.FALLING, callback=callback_switch_autonomous, bouncetime=50 )  
GPIO.add_event_detect( SWITCH_read_from_USBdrive, GPIO.FALLING, callback=callback_switch_read_from_USBdrive, bouncetime=50 )  
GPIO.add_event_detect( SWITCH_shutdown_RPi, GPIO.FALLING, callback=callback_switch_shutdown_RPi, bouncetime=50 )  
GPIO.add_event_detect( SWITCH_collect_data, GPIO.FALLING, callback=callback_switch_collect_data, bouncetime=50 ) 

initialize_RPi_Stuff()
	
turn_ON_LED( LED_boot_RPi )
GPIO.output( OUTPUT_to_relay, RELAY_ON )

while ( True ):	
	pass
	
	
