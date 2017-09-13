import sys
import time
import datetime
import picamera
import picamera.array
import numpy as np

time_format='%Y-%m-%d_%H:%M:%S'

class DataCollector(object):
  '''this object is passed to the camera.start_recording function, which will treat it as a 
      writable object, like a stream or a file'''
  def __init__(self):
    self.imgs=np.zeros((100, 64, 64, 3), dtype=np.uint8)
    self.idx=0
  
  def write(self, s):
    '''this is the function that is called every time the PiCamera has a new frame'''
    data=np.reshape(np.fromstring(s, dtype=np.uint8), (64, 64, 3), 'C')
    self.imgs[self.idx]=data
    self.idx+=1
    if self.idx == 100:
      self.idx=0
      self.flush()  
    #TODO this function should call all the serial stuff to communicate with the arduino
         # and check for button press to stop recording
  
  def flush(self):
    '''this function is called every time the PiCamera stops recording'''
    img_file='imgs_{0}'.format(datetime.datetime.now().strftime(time_format))
    np.savez(img_file, self.imgs)
    self.imgs[:]=0

collector=DataCollector()
try:
  with picamera.PiCamera() as camera:
    camera.resolution=(64, 64) #final image size
    camera.zoom=(.125, 0, .875, 1) #crop so aspect ratio is 1:1
    camera.framerate=10 #<---- framerate (fps) determines speed of data recording
    camera.start_preview() #TODO turn on using debug flag 
    camera.start_recording(collector, format='rgb')
    input('Press enter to stop recording') # will cause hang waiting for user input
    camera.stop_recording()
except:
    camera.stop_recording()
    print("Unexpected error: ", sys.exc_info()[0])

