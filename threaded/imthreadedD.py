import numpy as np
import cv2
import picamera
import threading
import time
import sys
import tensorflow as tf
import keras
import serial

print("setting up model")
from testmodel import model
model.load_weights('Nweights.h5')
model._make_predict_function()
graph=tf.get_default_graph()

steerstats=np.load('steerstats.npz')['arr_0']

try:
  print("connecting to serial port 0")
  ser=serial.Serial('/dev/ttyACM0')
except serial.SerialException:
  try:
    print("connecting to serial port 1")
    ser=serial.Serial('/dev/ttyACM1')
  except serial.SerialException:
    print("can't make serial connection")

imageData=np.zeros((78, 128, 3), dtype=np.uint8)
stopEvent=threading.Event()
lock=threading.Lock()

def imageprocessor(event):
  global imagedata
  global graph
  with graph.as_default():
    time.sleep(1)
    while not event.is_set():
      lock.acquire()
      tmpimg=np.copy(imageData)
      lock.release()
      immean=tmpimg.mean()
      imvar=tmpimg.std()
      #print('{0}, {1}'.format(immean, imvar))
      start=time.time()
      pred=model.predict(np.expand_dims(tmpimg, axis=0))
      end=time.time()
      if(end-start)<.2:
        time.sleep(.2-(end-start))
      end2=time.time()
      steer_command=pred[0][0]*steerstats[1]+steerstats[0]
      dataline='{0}, {1}, {2}, {3}\n'.format(1, int(steer_command), 1570, 0)
      print(dataline)
      try:
        ser.flushInput()
        ser.write(dataline.encode('ascii'))
        ser.readline()
        ser.readline()
        #print(ser.readline())
        #print(ser.readline())
      except:
        print("some serial problem")


class datagetter(object):
  def __init__(self):
    pass

  def write(self, s):
    global imageData
    imagerawdata=np.reshape(np.fromstring(s, dtype=np.uint8), (96, 128, 3), 'C')
    imdata=imagerawdata[0:78, :]
    immean=imdata.mean()
    imvar=imdata.std()
    lock.acquire()
    imageData=np.copy((imdata-immean)/imvar)
    lock.release()

  def flush(self):
    pass

try:
  dg=datagetter()
  with picamera.PiCamera() as camera:
    camera.resolution=(128, 96)
    camera.framerate=20
    camera.start_recording(dg, format='rgb')
    ipthread=threading.Thread(target=imageprocessor, args=[stopEvent])
    ipthread.start()
    input('press enter to stop recording')
    stopEvent.set()
    camera.stop_recording()
except:
  print("unexpected error: ", sys.exc_info()[0])
  camera.stop_recording()
  raise Exception('global exception')
finally:
  ipthread.join()
  ser.close()

