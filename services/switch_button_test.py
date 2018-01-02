#!/usr/bin/python3

import RPi.GPIO as GPIO  
import time


# Tests for new switches, LEDS and power relay

# -------- New Power On/Off functionality --------- 

1- User holds boot switch in ON position which energizes power relay coil ( power LED remains unlit )
2- Relay contacts close supplying 5 volts to Pi.
3- Pi boots, executes service program which also energizes relay coil
4- Pi turns on power LED to indicate to user that the Pi is under control
5- User releases toggle switch, but Pi has already latched relay contacts closed so it remains powered
6- Program continues to execute until user flips power off switch telling Pi to shut it down


#	CONSTANTS are in ALL CAPS

# -------- GPIO pin numbers for ottoMicro Car --------- 
LED_read_from_USBdrive = 2
LED_copy_to_USBdrive = 3
LED_collect_data = 4
LED_autonomous = 17
LED_shutdown_RPi = 27
LED_boot_RPi = 22

SWITCH_collect_data = 10
SWITCH_copy_to_USBdrive = 9
SWITCH_read_from_USBdrive = 11
SWITCH_run_autonomous = 5
SWITCH_shutdown_RPi = 6

OUTPUT_to_relay = 13

# -------- Button or switch (gadgets) constants --------- 
# switch push or switch position-up connects to ground, 
#  thus internal pull up  resistors are used  
ON = GPIO.LOW		# LOW signal on GPIO pin means switch is ON (up position)		
OFF = GPIO.HIGH		# HIGH signal on GPIO pin means switch is OFF (down position)
PUSHED = GPIO.LOW	# LOW signal on GPIO pin means switch is PUSHED
UP = GPIO.HIGH		# HIGH signal on GPIO pin means switch is UP

# -------- LED state constants --------- 
LED_ON = GPIO.HIGH
LED_OFF = GPIO.LOW

# -------- Kind of error constants --------- 
NONE = 0
WARNING = 1
FATAL = 2
NO_USB_DRIVE_WARNING = 3
AUTONOMOUS_WARNING = 4
RECORDED_DATA_NOT_SAVED = 5

GPIO.setmode( GPIO.BCM )  
GPIO.setwarnings( False )  

	
# -------- LED functions to make code clearer --------- 
def turn_ON_LED( which_LED ):
	GPIO.output( which_LED, LED_ON )

def turn_OFF_LED( which_LED ):
	GPIO.output( which_LED, LED_OFF )	
	
# -------- Functions called by gadget callback functions --------- 
def callback_switch_copy_to_USBdrive( channel ): 
	print( "copy_to_USBdrive" )
	
def callback_switch_read_from_USBdrive( channel ):
	print( "read_from_USBdrive" )
	 
def callback_switch_autonomous( channel ):  
	print( "run_autonomous" )
	 
def callback_switch_shutdown_RPi( channel ):
	print( "shutdown_RPi" )
	 
def callback_switch_collect_data( channel ):  
	print( "collect_data" )
	 	
# ------------------------------------------------- 
def initialize_RPi_Stuff():
	
	# blink LEDs as an alarm if either switch has been left in the ON (up) position
	LED_state = LED_ON

	while(( GPIO.input( SWITCH_shutdown_RPi ) == ON ) or ( GPIO.input( SWITCH_collect_data ) == ON )):
		GPIO.output( LED_shutdown_RPi, LED_state )
		GPIO.output( LED_collect_data, LED_state )
		time.sleep( .25 )
		LED_state = LED_state ^ 1		# XOR bit to turn LEDs off or on
	
	# turn off all LEDs for initialization
	turn_OFF_LED( LED_copy_to_USBdrive )
	turn_OFF_LED( LED_read_from_USBdrive )
	turn_OFF_LED( LED_collect_data )
	turn_OFF_LED( LED_shutdown_RPi )
	turn_OFF_LED( LED_autonomous )
	turn_OFF_LED( LED_boot_RPi )


# ---------------- MAIN PROGRAM ------------------------------------- 

GPIO.setmode( GPIO.BCM )  
GPIO.setwarnings( False )

#  falling edge detection setup for all gadgets ( switchs or switches ) 
GPIO.setup( SWITCH_copy_to_USBdrive, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( SWITCH_run_autonomous, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( SWITCH_read_from_USBdrive, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( SWITCH_shutdown_RPi, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( SWITCH_collect_data, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 

GPIO.setup( LED_read_from_USBdrive, GPIO.OUT )
GPIO.setup( LED_copy_to_USBdrive, GPIO.OUT )
GPIO.setup( LED_collect_data, GPIO.OUT )
GPIO.setup( LED_shutdown_RPi, GPIO.OUT )
GPIO.setup( LED_autonomous, GPIO.OUT )
GPIO.setup( LED_boot_RPi, GPIO.OUT )

GPIO.setup( OUTPUT_to_relay, GPIO.OUT )

# setup callback routines for gadget falling edge detection  
#	NOTE: because of a RPi bug, sometimes a rising edge will also trigger these routines!
GPIO.add_event_detect( SWITCH_copy_to_USBdrive, GPIO.FALLING, callback=callback_switch_copy_to_USBdrive, bouncetime=20 )  
GPIO.add_event_detect( SWITCH_run_autonomous, GPIO.FALLING, callback=callback_switch_autonomous, bouncetime=20 )  
GPIO.add_event_detect( SWITCH_read_from_USBdrive, GPIO.FALLING, callback=callback_switch_read_from_USBdrive, bouncetime=20 )  
GPIO.add_event_detect( SWITCH_shutdown_RPi, GPIO.FALLING, callback=callback_switch_shutdown_RPi, bouncetime=50 )  
GPIO.add_event_detect( SWITCH_collect_data, GPIO.FALLING, callback=callback_switch_collect_data, bouncetime=150 ) 

initialize_RPi_Stuff()

turn_ON_LED( OUTPUT_to_relay )
turn_ON_LED( LED_boot_RPi )


while ( True ):	
	turn_ON_LED( LED_read_from_USBdrive )
	turn_OFF_LED( LED_copy_to_USBdrive )
	turn_ON_LED( LED_collect_data )
	turn_OFF_LED( LED_autonomous )
	turn_ON_LED( LED_shutdown_RPi )
	time.sleep( .25 )

	turn_OFF_LED( LED_read_from_USBdrive )
	turn_ON_LED( LED_copy_to_USBdrive )
	turn_OFF_LED( LED_collect_data )
	turn_ON_LED( LED_autonomous )
	turn_OFF_LED( LED_shutdown_RPi )
	time.sleep( .25 )

	pass	
	
	
