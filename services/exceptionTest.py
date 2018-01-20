#!/usr/bin/python3

import sys, os

def this_fails():
	x = 1/0

try:
	this_fails()
	raise Exception( 5 , 'eggs')

except Exception as inst:
	if( len(inst.args) == 1 ):
		print (inst.args[0])
	else:
		print(inst.args[0])
		print(inst.args[1])
