import time
import picamera
import picamera.array
import numpy as np
import scipy 
import scipy.misc

imgArr=np.zeros((60, 3, 64, 64), dtype=np.uint8)
with picamera.PiCamera() as camera:
  with picamera.array.PiRGBArray(camera) as output:
    camera.resolution=(640, 480)
    
    for i, filename in enumerate(camera.capture_continuous(output, 'rgb', burst=True)) :
      #camera.capture(output, 'rgb')
      print('Captured %dx%d image' % (output.array.shape[1], output.array.shape[0]))
      img=output.array[:, 80:-80]
      output.truncate(0)
      img=scipy.misc.imresize(img, (64, 64), 'cubic', 'RGB').transpose(2, 0, 1)
      #print('%d %d %d' %(img.shape[0], img.shape[1], img.shape[2]))
      imgArr[i]=np.array(img, dtype=np.uint8)
      time.sleep(.01)
      if i==59: 
        break
    np.savez('testfile', imgArr)
