import os
import glob
import cv2
import numpy as np
#import matplotlib.pyplot as plt


#imagefiles=glob.glob(os.path.join('data', 'imgs_2017-09-14_22-2[2-5]*.npz'))
#ctlfiles=glob.glob(os.path.join('data', 'commands_2017-09-14_22-2[2-5]*.npz'))
imagefiles=glob.glob(os.path.join('data/pitts/add', 'imgs*.npz'))
ctlfiles=glob.glob(os.path.join('data/pitts/add', 'commands*.npz'))
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

strmax=max(steer)
strmin=min(steer)
print(np.argmin(steer))

#plt.plot(strange, steer, 'r', sprange, speed, 'b')
#plt.show()
for imagefile, ctlfile in zip(sorted(imagefiles), sorted(ctlfiles)):
  print(imagefile)
  print(ctlfile)
  images=np.load(imagefile)['arr_0']
  ctldata=np.load(ctlfile)['arr_0']
  steer=np.trim_zeros(ctldata[:, 0], trim='b')
  for im, steerval in zip(images, steer):
  #for im in images:
    im=im[0:78, :]
    image=cv2.resize(im, (0, 0), fx=5, fy=5, interpolation=cv2.INTER_NEAREST)
    r, g, b=cv2.split(image)
    newim=cv2.merge((b, g, r))
    newim2=cv2.copyMakeBorder(newim, 1, 20, 0, 0, cv2.BORDER_CONSTANT, value=[255, 255, 255])
    horzval=int(round(128*(steerval-strmin)/(strmax-strmin)))
    minval=int(round(128*float((strmin-strmin))/(strmax-strmin)))
    maxval=int(round(128*float((strmax-strmin))/(strmax-strmin)))
    print(horzval)
    print(steerval)
    cv2.circle(newim2, (5*horzval, 400), 5, [0, 0, 255], thickness=-1)
    cv2.circle(newim2, (5*minval, 400), 5, [255, 0, 255], thickness=-1)
    cv2.circle(newim2, (5*maxval, 400), 5, [255, 0, 255], thickness=-1)
    cv2.imshow("images", newim2)
    cv2.waitKey(100) 
