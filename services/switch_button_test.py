#!/usr/bin/python3


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

def callback_button_copy_to_SDcard( channel ): 
	pass
	
def callback_button_read_from_SDcard( channel ):
	pass
	 
def callback_button_autonomous( channel ):  
	pass
	 
def callback_switch_shutdown_RPi( channel ):
	pass
	 
def callback_switch_collect_data( channel ):  
	pass
	 
button = 0
switch = 1
	
switch_button_handler = {
#	"button_copy_to_SDcard":	button, button_copy_to_SDcard_pin, LED_copy_to_SDcard_pin, callback_button_copy_to_SDcard,
#	"button_read_from_SDcard":	button, button_read_from_SDcard_pin, LED_read_from_SDcard_pin, callback_button_read_from_SDcard,
#	"button_run_autonomous":	button, button_run_autonomous_pin, LED_autonomous_pin, callback_button_autonomous,
#	"switch_shutdown_RPi":		switch, switch_shutdown_RPi_pin, LED_shutdown_RPi_pin, callback_switch_shutdown_RPi,
	"switch_collect_data":		switch, switch_collect_data_pin, LED_collect_data_pin, callback_switch_collect_data
}

print( switch_button_handler )