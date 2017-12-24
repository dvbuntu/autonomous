#!/usr/bin/python3

import RPi.GPIO as GPIO  


# -------- GPIO pin numbers for ottoMicro Car --------- 
LED_copy_to_SDcard_pin = 2
LED_read_from_SDcard_pin = 3
LED_autonomous_pin = 4

button_copy_to_SDcard_pin = 17
button_read_from_SDcard_pin = 27
button_run_autonomous_pin = 22

switch_shutdown_RPi_pin = 10
switch_collect_data_pin = 9

# LEDpowerStatusOfRPi = hardwired to +3.3 volt pin #1 of RPi
LED_collect_data_pin = 5
LED_shutdown_RPi_pin = 6

GPIO.setmode( GPIO.BCM )  
GPIO.setwarnings( False )  

#  falling edge detection setup for all buttons and switches
GPIO.setup( button_copy_to_SDcard_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( button_run_autonomous_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( button_read_from_SDcard_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( switch_shutdown_RPi_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 
GPIO.setup( switch_collect_data_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP ) 

GPIO.setup( LED_copy_to_SDcard_pin, GPIO.OUT )
GPIO.setup( LED_read_from_SDcard_pin, GPIO.OUT )
GPIO.setup( LED_autonomous_pin, GPIO.OUT )
GPIO.setup( LED_shutdown_RPi_pin, GPIO.OUT )
GPIO.setup( LED_collect_data_pin, GPIO.OUT )

def callback_button_copy_to_SDcard( channel ): 
	print( switch_button_handler["copy_to_SDcard"] )
	
def callback_button_read_from_SDcard( channel ):
	print( switch_button_handler["read_from_SDcard"] )
	 
def callback_button_autonomous( channel ):  
	print( switch_button_handler["run_autonomous"] )
	 
def callback_switch_shutdown_RPi( channel ):
	print( switch_button_handler["shutdown_RPi"] )
	 
def callback_switch_collect_data( channel ):  
	print( switch_button_handler["collect_data"] )
	 	
switch_button_handler = {
	"copy_to_SDcard":	{ "type":"button", "gadgetPin":button_copy_to_SDcard_pin, "ledPin":LED_copy_to_SDcard_pin, "callRoutine":callback_button_copy_to_SDcard },
	"read_from_SDcard":	{ "type":"button", "gadgetPin":button_read_from_SDcard_pin, "ledPin":LED_read_from_SDcard_pin, "callRoutine":callback_button_read_from_SDcard },
	"run_autonomous":	{ "type":"button", "gadgetPin":button_run_autonomous_pin, "ledPin":LED_autonomous_pin, "callRoutine":callback_button_autonomous },
	"shutdown_RPi":		{ "type":"switch", "gadgetPin":switch_shutdown_RPi_pin, "ledPin":LED_shutdown_RPi_pin, "callRoutine":callback_switch_shutdown_RPi },
	"collect_data":		{ "type":"switch", "gadgetPin":switch_collect_data_pin, "ledPin":LED_collect_data_pin, "callRoutine":callback_switch_collect_data }
}

GPIO.add_event_detect( button_copy_to_SDcard_pin, GPIO.FALLING, callback=callback_button_copy_to_SDcard, bouncetime=300 )  
GPIO.add_event_detect( button_run_autonomous_pin, GPIO.FALLING, callback=callback_button_autonomous, bouncetime=300 )  
GPIO.add_event_detect( button_read_from_SDcard_pin, GPIO.FALLING, callback=callback_button_read_from_SDcard, bouncetime=300 )  
GPIO.add_event_detect( switch_shutdown_RPi_pin, GPIO.FALLING, callback=callback_switch_shutdown_RPi, bouncetime=300 )  
GPIO.add_event_detect( switch_collect_data_pin, GPIO.FALLING, callback=callback_switch_collect_data, bouncetime=300 ) 

print( switch_button_handler["copy_to_SDcard"]["buttonPin"] )

while( True ):
	pass
	
	