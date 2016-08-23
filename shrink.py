import os
import math
import numpy as np
import h5py
import glob
from tqdm import tqdm
import scipy

import matplotlib.pyplot as plt
from keras.utils.np_utils import to_categorical
dfiles = glob.glob('data/*.h5')

all_imgs = []
all_speedx = []
all_targets = []

from gas import make_cat

for dfile in dfiles:
    with h5py.File(dfile,'r') as h5f:
        # raw data
        A = dict(h5f.items()) 
        # extract images in 1-byte format
        B = np.array(A['images'].value,dtype=np.float16)/255.
        # change BGR to RGB
        B = B[:,::-1,:,:]
        # Scale down image size
        imgs = np.zeros((len(B),3,64,64),dtype=np.float16)
        for i,b in enumerate(B):
            imgs[i] = scipy.misc.imresize(b,(64,64),'cubic','RGB').transpose((2,0,1))
        # speed and accel scale
        speedx = A['vehicle_states'].value[:,2:4]
        speedx[:,0] = (speedx[:,0] - speedmin) / (speedmax-speedmin)
        speedx[:,1] = (speedx[:,1] - accelmin) / (accelmax-accelmin)
        # throttle and steering scale
        targets_cat = list(map(make_cat, (A['targets'].value[:,5] + 1) / 2.))
        targets = to_categorical(targets_cat,3)
        all_imgs.extend(np.array(imgs,dtype=np.uint8))
        all_speedx.extend(np.array(speedx,dtype=np.float32))
        all_targets.extend(np.array(targets_cat,dtype=np.uint8))

imgs_arr = np.array(all_imgs)
speedx_arr = np.array(all_speedx)
targets_arr = np.array(all_targets)

imgs_arr.savez('data/imgs_arr.npz')
speedx_arr.savez('data/speedx_arr.npz')
targets_arr.savez('data/targets_arr.npz')
