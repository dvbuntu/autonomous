import serial
import time
import picamera
import picamera.array
import numpy as np

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

strvals=[1100+x*100 for x in range(0, 9)]

class DataProcessor(object):
  '''this object is passed to the camera.start_recording function'''
  strvals=[1100+x*100 for x in range(0, 9)]
  index=0
  def __init__(self):
    pass

  def write(self, s):
    '''this function gets called every time the camera has a new frame'''
    #imdatat=np.reshape(np.fromstring(s, dtype=np.uint8), (96, 128, 3), 'C')  
    #imdata=imdatat[0:78, :]
    #immean=imdata.mean()
    #imvar=imdata.std()
    dataline='{0}, {1}, {2}, {3}\r\n'.format(1, self.strvals[self.index], 1550, 0)
    self.index=(self.index+1)%len(self.strvals)
    print(dataline)
    try: 
      ser.flushInput()
      ser.write(dataline.encode('ascii'))
      ser.flushOutput()
      print(ser.readline())
      print(ser.readline())
      print(ser.readline())
      print(ser.readline())
      print(ser.readline())
	
    except: 
      print("couldn't write, moving on") 

  def flush(self):
    pass
  
try:
  Processor=DataProcessor()
  with picamera.PiCamera() as camera:
    camera.resolution=(128, 96)
    camera.framerate=2
    camera.start_recording(Processor, format='rgb')
    input('press enter to stop recording')
    camera.stop_recording()
    
except:
  print("Unexpected error: ", sys.exc_info()[0])
  camera.stop_recording()
  raise Exception('global exception')

finally:
    # cleanup
    ser.close()

'''
for i in strvals:
  dataline='{0}, {1}, {2}, {3}\n\n'.format(1, int(i), 1575, 0)
  print(dataline)
  ser.flushInput()
  ser.write(dataline.encode('ascii'))
  print(ser.readline())
  print(ser.readline())
  print(ser.readline())
  print(ser.readline())
  print(ser.readline())
  time.sleep(1)

dataline='{0}, {1}, {2}, {3}\n\n'.format(1, 1550, 1525, 0)
print(dataline)
ser.flushInput()
ser.write(dataline.encode('ascii'))
'''
