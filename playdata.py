import numpy as np
import cv2
import argparse


parser = argparse.ArgumentParser(description='Play the collected data.')
parser.add_argument('-f','--data_dir', action='store', default='data')

args = parser.parse_args()


# last 10% of every file provides validation...
img_files = glob.glob(os.path.join([data_dir,'imgs*.npz']))
speedx_files = glob.glob(os.path.join([data_dir,'speedx*.npz']))
target_files = glob.glob(os.path.join([data_dir,'targets*.npz']))

for i,s,t in zip(img_files, speedx_files, target_files):
  imgs = np.load(i)['arr_0']
  speedx = np.load(s)['arr_0']
  targets = np.load(t)['arr_0']


