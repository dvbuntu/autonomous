import threading
import numpy as np
import serial
import RPi.GPIO as GPIO
import time

try:
  print("connecting to serial port 0")
  ser = serial.Serial('/dev/ttyACM0')
except serial.SerialException:
  try:
    print("connecting to serial port 1")
    ser=serial.Serial('/dev/ttyACM1')
  except serial.SerialException:
    print('can not connect to serial port')
ser.writeTimeout = 3

dataline='{0}, {1}, {2}, {3}\n\n'.format(1, 1500, 1500, 0)
print(dataline)
ser.flushInput()
ser.write(dataline.encode('ascii'))
print(ser.readline())
#print(ser.readline())
#print(ser.readline())
#print(ser.readline())
#print(ser.readline())

