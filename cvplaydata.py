import os
import glob
import cv2
import numpy as np
import matplotlib.pyplot as plt


#imagefiles=glob.glob(os.path.join('data', 'imgs_2017-09-14_22-2[2-5]*.npz'))
#ctlfiles=glob.glob(os.path.join('data', 'commands_2017-09-14_22-2[2-5]*.npz'))
imagefiles=glob.glob(os.path.join('data', 'imgs*.npz'))
ctlfiles=glob.glob(os.path.join('data', 'commands*.npz'))
print(len(imagefiles))

speed=np.array([])
steer=np.array([])

for ctlfile in sorted(ctlfiles):
  ctldata=np.load(ctlfile)['arr_0']
  steer=np.concatenate((steer, np.trim_zeros(ctldata[:, 0], trim='b')), axis=0)
  speed=np.concatenate((speed, np.trim_zeros(ctldata[:, 1], trim='b')), axis=0)

if len(speed)>0:
  print('for the steering data, the maximum value is {}, and the minimum value is {}'.format(max(steer), min(steer)))
  print('the average steering value is {}'.format(np.mean(steer)))
  print('for the speeding data, the maximum value is {}, and the minimum value is {}'.format(max(speed), min(speed)))
  print('the average speeding value is {}'.format(np.mean(speed)))

strange=np.arange(0, len(steer))
sprange=np.arange(0, len(speed))

plt.plot(strange, steer, 'r', sprange, speed, 'b')
plt.show()
'''
for imagefile in sorted(imagefiles):
  print(imagefile)
  images=np.load(imagefile)['arr_0']
  for im in images:
    image=cv2.resize(im, (0, 0), fx=5, fy=5, interpolation=cv2.INTER_NEAREST)
    cv2.imshow("images", image)
    cv2.waitKey(100) 
'''
