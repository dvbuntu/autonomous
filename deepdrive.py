import os
import math
import numpy as np
import h5py
import glob
from tqdm import tqdm
import scipy

import keras
from keras.models import Sequential, Model
from keras.layers.core import Dense, Dropout, Activation, Flatten, Reshape
from keras.layers import Embedding, Input, merge
from keras.layers.recurrent import SimpleRNN, LSTM
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.optimizers import SGD, Adam, RMSprop
import sklearn.metrics as metrics

import matplotlib.pyplot as plt
plt.ion()

# Read in deep drive data
dfiles = glob.glob('data/*.h5')

# 999 data points, images are 3x227x227
# vehicle_states are just target at previous time
# no distance finder, but this is enough to work with
dfile = dfiles[0]
h5f = h5py.File(dfile,'r')
A = dict(h5f.items()) 

# view image
plt.imshow(A['images'].value[0].swapaxes(0,2).swapaxes(0,1))
AA = A['images'].value

# look at targets
A['targets'].value[:2]
A['vehicle_states'].value[:2]

at = A['targets'].value[:-1]
av = A['vehicle_states'].value[1:]

# slim inputs
B = np.array(A['images'].value,dtype=np.uint8)
# inverted color!
plt.imshow(255 - B[0].swapaxes(0,2).swapaxes(0,1))
plt.imshow(B[0].swapaxes(0,2).swapaxes(0,1))
plt.imshow(AA[0].swapaxes(0,2).swapaxes(0,1))

# blue channel inverted?
inv = np.copy(B[0])
inv = 255 - inv
inv[2] = 255 - inv[2]
plt.imshow(inv.swapaxes(0,2).swapaxes(0,1))
plt.imshow(B[0].swapaxes(0,2).swapaxes(0,1))

bb = scipy.misc.imresize(B[0],(128,128),'cubic','RGB')
plt.imshow(bb)

aa = scipy.misc.imresize(AA[0],(128,128),'cubic','RGB')
plt.imshow(aa)

ndata = 0
for dfile in dfiles:
    with h5py.File(dfile,'r') as h5f:
        label_list = list()
        # Get data size
        for k,v in h5f.items():
            ndata += v.shape[0]
            label_list.append(k)
        shape = (ndata, v.shape[1], v.shape[2])
        data = np.zeros(shape,dtype=np.uint8)
        # one-hot encoded
        labels = np.zeros((shape[0],len(h5f.values())),dtype=np.float16)
        # For every font
        for i,(k,v) in tqdm(enumerate(h5f.items()),total=len(label_list)):
            label = label_list.index(k)
            data[i*v.shape[0]:(i+1)*v.shape[0]]=v[:]
            labels[i*v.shape[0]:(i+1)*v.shape[0],label] = 1.



# frame size
nrows = 16
ncols = 16

# accel, speed, distance, angle
real_in = Input(shape=(4,), name='real_input')

# video frame in, grayscale
frame_in = Input(shape=(1,nrows,ncols))

# convolution for image input
conv = Convolution2D(1,3,3,border_mode='same',
        activation='relu')
conv_l = conv(frame_in)
pool_l = MaxPooling2D(pool_size=(2,2))(conv_l)

flat = Flatten()(pool_l)

M = merge([flat,real_in], mode='concat', concat_axis=1)

A = Dense(1, activation='linear')(M)
P = Dense(1, activation='linear')(M)

model = Model(input=[real_in, frame_in], output=[A,P])

model.compile(loss='mean_squared_error',
              optimizer='rmsprop',
              metrics=['accuracy'])

nsamples = 1000
fake_real = np.random.random((nsamples,4))
fake_frame = np.random.random((nsamples,1,nrows,ncols))

fake_A = np.random.random(nsamples)
fake_P = np.random.random(nsamples)

h = model.fit([fake_real, fake_frame], [fake_A, fake_P], batch_size = 32, nb_epoch=10, verbose=1)


