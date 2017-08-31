# Play training files

import os
import numpy as np
import glob
import cv2
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import argparse
import time

img_file = 'testfile.npz'

plt.ion()

imgs = np.load(img_file)['arr_0']


print('imgs: ', imgs.shape)
# print(imgs)
for im in imgs:
  #print(im.shape)
  # print(im)
  # cv2.imshow('im', im)
  plt.imshow(im.transpose(1,2,0))
  plt.pause(0.001)
  plt.draw()

plt.close()





