import h5py
import scipy
import scipy.misc
import glob
import numpy as np
from tqdm import tqdm

import matplotlib.pyplot as plt
plt.ion()


camfiles = sorted(glob.glob('dataset/camera/*.h5'))
logfiles = sorted(glob.glob('dataset/log/*.h5'))

all_imgs = np.zeros((1,3,64,64),dtype=np.uint8)
spds = np.zeros(1)
accel = np.zeros(1)
steer = np.zeros(1)
gas = np.zeros(1)
brake = np.zeros(1)

fstarts = [0]

for c,l in zip(camfiles,logfiles):
    cams = h5py.File(c,'r')['X']

    # How much data are we talking about in this file?  Keep track
    nframes = len(cams)
    abs_start = fstarts[-1]
    abs_end = abs_start + nframes
    fstarts.append(abs_end)

    # strip down cams to 64x64
    smcam = np.zeros((nframes,3,64,64),dtype=np.uint8)
    for i,c in tqdm(enumerate(cams)):
        smcam[i] = scipy.misc.imresize(c[:,:,80:-80],(64,64),'cubic','RGB').transpose((2,0,1))

    logs = h5py.File(l,'r')
    ptrs = logs['cam1_ptr'].value

    # Line logs up to correct frames
    starts = np.zeros(nframes,dtype=np.uint32)
    starts[0] = 37
    cur = 1
    for i,p in enumerate(ptrs):
        if int(p) == cur:
            starts[cur] = i
            cur += 1

    # Make room for new data
    all_imgs.resize((abs_end, 3, 64, 64))
    spds.resize((abs_end))
    accel.resize((abs_end))
    steer.resize((abs_end))
    gas.resize((abs_end))
    brake.resize((abs_end))

    # Stuff data into large array
    all_imgs[abs_start:abs_end] = smcam
    spds[abs_start:abs_end] = logs['speed'].value[starts]
    accel[abs_start:abs_end] = logs['car_accel'].value[starts]
    steer[abs_start:abs_end] = logs['steering_angle'].value[starts]
    gas[abs_start:abs_end] = logs['gas'].value[starts]
    brake[abs_start:abs_end] = logs['brake'].value[starts]

# scale
spds = (spds - np.min(spds))/(np.max(spds)-np.min(spds))
accel = (accel - np.min(accel))/(np.max(accel)-np.min(accel))
steer = (steer - np.min(steer))/(np.max(steer)-np.min(steer))
gas = (gas - np.min(gas))/(np.max(gas)-np.min(gas))
brake = (brake - np.min(brake))/(np.max(brake)-np.min(brake))

np.savez('simple_data.npz',
        imgs=all_imgs,
        spds=spds,
        accel=accel,
        steer=steer,
        gas=gas,
        brake=brake,
        idx = np.array(fstarts))

