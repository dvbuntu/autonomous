# Play training files

import os
import numpy as np
import glob
import cv2
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import argparse
import time

print("Finding data files")

parser = argparse.ArgumentParser(description='Play Otto collected data')
parser.add_argument('-f','--data-dir', action='store', default='data')
args = parser.parse_args()
data_dir = args.data_dir

img_files = glob.glob(os.path.join(data_dir,'imgs*.npz'))
speedx_files = glob.glob(os.path.join(data_dir,'speedx*.npz'))
target_files = glob.glob(os.path.join(data_dir,'targets*.npz'))

plt.ion()

for i,s,t in zip(sorted(img_files), sorted(speedx_files), sorted(target_files)):
  print(i, s, t)
  imgs = np.load(i)['arr_0']
  speedx = np.load(s)['arr_0']
  targets = np.load(t)['arr_0']

  
  print('imgs: ', imgs.shape)
  # print(imgs)
  for im in imgs:
    #print(im.shape)
    # print(im)
    # cv2.imshow('im', im)
    plt.imshow(im.transpose(1,2,0))
    plt.pause(0.01)
    plt.draw()

plt.close()





