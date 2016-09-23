import h5py
import scipy
import scipy.misc
import glob
from tqdm import tqdm

import keras
from keras.models import Sequential, Model
from keras.layers.core import Dense, Dropout, Activation, Flatten, Reshape
from keras.layers import Embedding, Input, merge, ELU
from keras.layers.recurrent import SimpleRNN, LSTM
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.optimizers import SGD, Adam, RMSprop
from keras.regularizers import l2, activity_l2, l1
from keras.utils.np_utils import to_categorical
from keras import backend as K
import sklearn.metrics as metrics

import matplotlib.pyplot as plt
plt.ion()


camfiles = sorted(glob.glob('dataset/camera/*.h5'))
logfiles = sorted(glob.glob('dataset/log/*.h5'))

cams = h5py.File(camfiles[2],'r')['X'].value
nframes = len(cams)

# strip down cams to 64x64
smcam = np.zeros((nframes,3,64,64),dtype=np.uint8)
for i,c in tqdm(enumerate(cams)):
    smcam[i] = scipy.misc.imresize(c[:,:,80:-80],(64,64),'cubic','RGB').transpose((2,0,1))

logs = h5py.File(logfiles[2],'r')
ptrs = logs['cam1_ptr'].value

starts = np.zeros(nframes,dtype=np.uint32)
starts[0] = 37
cur = 1
for i,p in enumerate(ptrs):
    if int(p) == cur:
        starts[cur] = i
        cur += 1

spds = logs['speed'].value[starts]
accel = logs['car_accel'].value[starts]
steer = logs['steering_angle'].value[starts]
gas = logs['gas'].value[starts]
brake = logs['brake'].value[starts]

np.savez('simple_data.npz',
        imgs=smcam,
        spds=spds,
        accel=accel,
        steer=steer,
        gas=gas,
        brake=brake)

