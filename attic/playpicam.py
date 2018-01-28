# Play training files

import os
import numpy as np
import glob
import cv2
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import argparse
import time

#img_file = 'testfile.npz'
img_files = glob.glob('imgs*.npz')

plt.ion()

#imgs = np.load(img_file)['arr_0']

for i in img_files :
  imgs = np.load(i)['arr_0']
  print('imgs: ', imgs.shape)
  idx=0
  for im in imgs:
    #plt.imshow(im.transpose(1,2,0))
    plt.imshow(im)
    plt.pause(0.001)
    plt.draw()
    print(idx)
    idx+=1

plt.close()





