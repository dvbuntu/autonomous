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
import shutil

import logging
logging.basicConfig(filename='/tmp/ottoMicroLogger.log',level=logging.DEBUG)
logging.debug( '\n\n new session \n' )

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

# --------Old Data Collection Command Line Startup Code--------- 
time_format='%Y-%m-%d_%H-%M-%S'

#	**** fubarino not connected yet for debugging purposes ****
#	Opens serial port to the arduino:
try:
	ser=serial.Serial('/dev/ttyACM0')
	logging.debug( 'opened serial port' )
	
except Exception as the_bad_news:				
	handle_exception( the_bad_news ) 
	
# -------------- Data Collector Object -------------------------------  

NUM_FRAMES = 100

class DataCollector(object):
	'''this object is passed to the camera.start_recording function, which will treat it as a 
	writable object, like a stream or a file'''
	def __init__(self):
		self.imgs=np.zeros((NUM_FRAMES, 96, 128, 3), dtype=np.uint8) #we put the images in here
		self.IMUdata=np.zeros((NUM_FRAMES, 7), dtype=np.float32) #we put the imu data in here
		self.RCcommands=np.zeros((NUM_FRAMES, 2), dtype=np.float16) #we put the RC data in here
		self.idx=0 # this is the variable to keep track of number of frames per datafile
		nowtime=datetime.datetime.now()
		self.img_file='/home/pi/autonomous/data/imgs_{0}'.format(nowtime.strftime(time_format))
		self.IMUdata_file='/home/pi/autonomous/data/IMU_{0}'.format(nowtime.strftime(time_format))
		self.RCcommands_file='/home/pi/autonomous/data/commands_{0}'.format(nowtime.strftime(time_format))

	def write(self, s):
		'''this is the function that is called every time the PiCamera has a new frame'''
		imdata=np.reshape(np.fromstring(s, dtype=np.uint8), (96, 128, 3), 'C')
		#now we read from the serial port and format and save the data:
		try:
			ser.flushInput()
			datainput=ser.readline()
			data=list(map(float,str(datainput,'ascii').split(','))) #formats line of data into array
#			logging.debug( data )
#			logging.debug( 'got cereal\n' )

		except:
			raise Exception( 11, 'exception in data collection write' )
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
			
		if ((self.idx % 20 ) == 0 ): 	# blink the LED everytime 20 frames are recorded
			turn_OFF_LED( LED_collect_data )
			time.sleep( .2)
			turn_ON_LED( LED_collect_data )

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
		logging.debug( 'OK: camera flush')
		

# -------- Switch / Button use cheatsheet --------- 
#
# Switch / Button		STATE		MEANING
# --------------------------------------------------------------
# SWITCH_boot_RPi		up		Energize power relay to Pi -> Boot Pi		
#				down		normal RPi operation
#
# SWITCH_shutdown_RPi		momentary up	Tried to shutdown Pi, if Data folder unsaved, blink all LEDs as warning
#						otherwise go through normal shutdown
#	after warning LEDs blinking:					
#				up, but not held	go back to normal RPi operation
#				up, and held	go through shutdown without saving Data folder
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
#	on startup:
# autonomous LED blinking on startup			autonomous switch was left in the up position
# collect data LED blinking on startup			collect data switch was left in the up position

#	in normal operation:
# all LEDs blinking					Tried to shutdown without first saving Data folder
# read and save LEDs blinking together			USB drive not mounted - insert or remove and insert USB drive

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
g_collector=DataCollector()
g_camera = picamera.PiCamera()
#	Note: these are just parameters to set up the camera, so the order is not important
g_camera.resolution=(96, 128) #final image size
# g_camera.zoom=(.125, 0, .875, 1) #crop so aspect ratio is 1:1
g_camera.framerate=10 #<---- framerate (fps) determines speed of data recording

def at_least_one_switch_is_up():
	if(( GPIO.input( SWITCH_save_to_USBdrive ) == SWITCH_UP ) or ( GPIO.input( SWITCH_autonomous ) == SWITCH_UP )
			or ( GPIO.input( SWITCH_read_from_USBdrive ) == SWITCH_UP ) or ( GPIO.input( SWITCH_shutdown_RPi ) == SWITCH_UP )
			or ( GPIO.input( SWITCH_collect_data ) == SWITCH_UP )):	
		return True
	else:
		return False
		
def all_switches_are_down():
	if( at_least_one_switch_is_up()):
		return False
	else:
		return True
				
# -------- Handler for clearing all switch errors --------- 
def handle_exception( the_bad_news ):
	global g_Current_Exception_Not_Finished

	if( g_Current_Exception_Not_Finished ):
		logging.debug( '*** another exception occurred, last exception not finished' )		
	else: 
		logging.debug( '\n' )		
		logging.debug( '*** Exception occurred' )		
		g_Current_Exception_Not_Finished = True
		if( len(the_bad_news.args) == 1 ):		# one argument exceptions are unforeseen 
			error_number = 15
			message = the_bad_news.args[0]
			logging.debug( str(the_bad_news.args[0]))
			
			exc_type, exc_obj, exc_tb = sys.exc_info()
			logging.debug(' line number = ' + str(exc_tb.tb_lineno))
		else:					# two argument exceptions are previously setup to be handled
			error_number = the_bad_news.args[0]
			message = the_bad_news.args[1]			
			logging.debug( 'error number = ' + str(the_bad_news.args[0]) + ': ' + str(the_bad_news.args[1]))
			
		blinkSpeed = .2
		switch_on_count = 3
		
		# blink the error number in the LEDs until the user holds down the button for 3 seconds
		LED_state = LED_ON
		error_not_cleared = True
		if( error_number > 31 ):	# bigger than this, we've run out of LEDs
			error_number = 31
			
		while( error_not_cleared ):	
			if( at_least_one_switch_is_up()):	# holding any switch up for long enough will clear error
				switch_on_count = switch_on_count - 1
				if( switch_on_count <= 0 ):
					error_not_cleared = False			
			if( LED_state == LED_ON ):		# put error_number in binary on the LEDs	
				LED_state = error_number & 0b00001
				GPIO.output( LED_read_from_USBdrive, LED_state )
				LED_state = ( error_number & 0b00010 ) >> 1
				GPIO.output( LED_save_to_USBdrive, LED_state )
				LED_state = ( error_number & 0b00100 ) >> 2
				GPIO.output( LED_collect_data, LED_state )
				LED_state = ( error_number & 0b01000 ) >> 3
				GPIO.output( LED_autonomous, LED_state )
				LED_state = ( error_number & 0b10000 ) >> 4
				GPIO.output( LED_shutdown_RPi, LED_state )
				LED_state = LED_OFF	
			else:
				turn_OFF_all_LEDs_except_BOOT()	
				LED_state = LED_ON	
			
			time.sleep( blinkSpeed )

		turn_OFF_all_LEDs_except_BOOT()		# show the user the error has been cleared
	
		# don't leave until we're sure user released button	
		while True:
			time.sleep( blinkSpeed )		# executes delay at least once
			if ( all_switches_are_down()): break
	
		logging.debug( "*** exception cleared by user\n" )
		g_Current_Exception_Not_Finished = False
		 	
# ------------------------------------------------- 
def callback_switch_collect_data( channel ):  
	global g_Recorded_Data_Not_Saved
	global g_Wants_To_See_Video
	global g_Camera_Is_Recording
	global g_camera
	global g_collector
		
	if( GPIO.input( SWITCH_collect_data ) == SWITCH_UP ):
		if( g_Camera_Is_Recording == False ):
			try:
				turn_ON_LED( LED_collect_data )					
				g_camera.start_recording( g_collector, format='rgb' )
				g_Camera_Is_Recording = True
				logging.debug( '* camera is recording' )
				if ( g_Wants_To_See_Video ):
					g_camera.start_preview() #displays video while it's being recorded

			except Exception as the_bad_news:				
				handle_exception( the_bad_news )
			
		else:
			logging.debug( '* warning: while recording, another rising transition detected on the collect data switch' )
		
	else:	# a collect data switch down position has occurred		
		if( g_Camera_Is_Recording == True ):
			logging.debug( '* recording and now switch is down' )
			try:
				if ( g_Wants_To_See_Video ):
					g_camera.stop_preview()
				g_camera.stop_recording()			
				logging.debug( 'OK: Camera recorded' )

			except Exception as the_bad_news:				
				handle_exception( the_bad_news )
				logging.debug( 'NG: Camera NOT recorded' )
				
			finally:
				g_Camera_Is_Recording = False
				g_Recorded_Data_Not_Saved = True
				turn_OFF_LED( LED_collect_data )
				logging.debug( 'exiting collect data' )

		else:
			#	this should not happen
			raise Exception( 31, 'NOT recording and a FALLING transition detected on the collect data switch' )
		 
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
			
			# 	check to see if the USB drive is mounted
			if( os.path.ismount( '/mnt/usbdrive' )):
				logging.debug( 'OK: USB drive is mounted' )
			
			elif(os.path.exists( '/dev/sda1')):
				call ( 'mount /mnt/usbdrive', shell=True )
				logging.debug( 'OK: USB drive is remounted' )
			else:
				raise Exception( 3, 'error: USB drive not mounted at /mnt/usbdrive' )
								
			pi_data_folder_path = '/home/pi/autonomous/data'
			nowtime=datetime.datetime.now()
			usb_path_with_index = '/mnt/usbdrive/data_{0}'.format(nowtime.strftime(time_format))
			shutil.copytree( pi_data_folder_path, usb_path_with_index )
			logging.debug( 'OK: folder copied to ' + usb_path_with_index )
			
			call ( 'umount /mnt/usbdrive', shell=True )
			logging.debug( 'OK: USB drive unmounted' )
			logging.debug( 'OK: data saved to USB' )
				
													
		except Exception as the_bad_news:				
			handle_exception( the_bad_news )
			logging.debug( 'NG: data NOT saved to USB' )
			
		finally:
			g_No_Callback_Function_Running = True
			turn_OFF_LED( LED_save_to_USBdrive )
			logging.debug( 'exiting save to USB drive' )

	else: 
		logging.debug( 'callback skipped: falling edge of save_to_USBdrive' )
	
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
			logging.debug( 'attempting to read /mnt/usbdrive/weights.h5' )
			
			# 	check to see if the USB drive is mounted
			if( os.path.ismount( '/mnt/usbdrive' )):
				logging.debug( 'OK: USB drive is mounted' )
			
			elif(os.path.exists( '/dev/sda1')):
				call ( 'mount /mnt/usbdrive', shell=True )
				logging.debug( 'OK: USB drive is remounted' )
			else:
				raise Exception( 3, 'error: USB drive not mounted at /mnt/usbdrive' )
			
			usb_training_file_path = '/mnt/usbdrive/weights.h5'
			pi_training_file_path = '/home/pi/autonomous/nntrain/weights.h5'

			shutil.copy2( usb_training_file_path, pi_training_file_path )	
			logging.debug( 'OK: file copied ' + usb_training_file_path + ' to ' + pi_training_file_path )
			
			call ( 'umount /mnt/usbdrive', shell=True )
			logging.debug( 'OK: USB drive unmounted' )
			logging.debug( 'OK: data read from USB' )
							
		except Exception as the_bad_news:				
			handle_exception( the_bad_news )
			logging.debug( 'NG: data NOT read from USB' )
			
		finally:
			g_No_Callback_Function_Running = True
			turn_OFF_LED( LED_read_from_USBdrive )
			logging.debug( 'exiting read from USB drive' )
	else: 
		logging.debug( 'callback skipped: falling edge of read_from_USBdrive' )
	 
# ------------------------------------------------- 
def callback_switch_autonomous( channel ):  
	global g_No_Callback_Function_Running

	# don't reenter an already running callback and don't respond to a high to low switch transition
	if(( g_No_Callback_Function_Running ) and ( GPIO.input( SWITCH_autonomous ) == SWITCH_UP )): 
		g_No_Callback_Function_Running = False
				
		try:
			turn_ON_LED( LED_autonomous )
			time.sleep( .1 )		# debounce switch some more
			# do the autonomous ....
			logging.debug( 'from autonmous:' )
			raise Exception( 8, 'autonomous function not implemented yet' )
			logging.debug( 'OK: automonous successful' )			
	
		except Exception as the_bad_news:				
			while( GPIO.input( SWITCH_autonomous ) == SWITCH_UP ): 	# wait for user to flip switch down before thowing error
				pass
				
			handle_exception( the_bad_news )
			logging.debug( 'NG: automonous failure' )			
			
		finally:
			g_No_Callback_Function_Running = True
			turn_OFF_LED( LED_autonomous )
			logging.debug( 'exiting autonomous' )
		
	else: 
		logging.debug( 'skipped: another callback from autonomous' )

# ------------------------------------------------- 
#	regular exception handling not used with shutdown function
def callback_switch_shutdown_RPi( channel ):
	global g_Recorded_Data_Not_Saved
	global g_No_Callback_Function_Running

	# don't reenter an already running callback and don't respond to a high to low switch transition
	if(( g_No_Callback_Function_Running ) and ( GPIO.input( SWITCH_shutdown_RPi ) == SWITCH_UP )): 
		g_No_Callback_Function_Running = False
		logging.debug( 'starting shutdown' )		
		
		while( GPIO.input( SWITCH_shutdown_RPi ) == SWITCH_UP ):	# wait for user to release switch
			pass
			
		time.sleep( .1 )	# debounce switch				
			
		if( g_Recorded_Data_Not_Saved ):
			blinkSpeed = .2
			pushed_up_count = 15
			LEDs_state = LED_ON
			shutdown_is_wanted = False
		else:
			shutdown_is_wanted = True
		
		#----------------------------------------------
		#	Recorded data is not saved, check to see if user really wants to shutdown without saving
		if( shutdown_is_wanted == False ):
			user_has_not_reacted = True												
			
			while( True ):		# loop until break
				if( LEDs_state == LED_ON ):	# blink all lights to signify data is unsaved
					turn_ON_all_LEDs()
					LEDs_state = LED_OFF		
				else:
					turn_OFF_all_LEDs()
					LEDs_state = LED_ON
					
				time.sleep( blinkSpeed )					

				if( user_has_not_reacted ):
					if( GPIO.input( SWITCH_shutdown_RPi ) == SWITCH_UP ):	# pushed up yet?
						user_has_not_reacted = False			# user has finally pushed switch up		
			
				# switch has been pushed up again
				else:	
					if( GPIO.input( SWITCH_shutdown_RPi ) == SWITCH_UP ):	# still pushed up?
						pushed_up_count = pushed_up_count - 1
					
						if( pushed_up_count <= 0 ):								
							shutdown_is_wanted = True
							break			# switch was pushed up long enough				 
					else:							
						shutdown_is_wanted = False
						break				# switch was pushed up but not for long enough																			
		#----------------------------------------------
							
		if( shutdown_is_wanted ):
			# shut down pi, data saved or not
			turn_OFF_all_LEDs()		# show the user the error has been cleared
			GPIO.output( OUTPUT_to_relay, RELAY_OFF )
			logging.debug( 'calling pi shutdown' )
			os.system( 'shutdown now -h' )
		
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
def turn_OFF_all_LEDs_except_BOOT():
	turn_OFF_LED( LED_save_to_USBdrive )
	turn_OFF_LED( LED_read_from_USBdrive )
	turn_OFF_LED( LED_collect_data )
	turn_OFF_LED( LED_shutdown_RPi )
	turn_OFF_LED( LED_autonomous )
	 	
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
	global g_camera
	
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
GPIO.add_event_detect( SWITCH_autonomous, GPIO.BOTH, callback=callback_switch_autonomous, bouncetime=50 )  
GPIO.add_event_detect( SWITCH_read_from_USBdrive, GPIO.FALLING, callback=callback_switch_read_from_USBdrive, bouncetime=50 )  
GPIO.add_event_detect( SWITCH_shutdown_RPi, GPIO.FALLING, callback=callback_switch_shutdown_RPi, bouncetime=50 )  
GPIO.add_event_detect( SWITCH_collect_data, GPIO.BOTH, callback=callback_switch_collect_data, bouncetime=50 ) 

initialize_RPi_Stuff()
	
turn_ON_LED( LED_boot_RPi )
GPIO.output( OUTPUT_to_relay, RELAY_ON )

while ( True ):	
	pass
	
	
