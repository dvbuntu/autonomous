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
plt.imshow(B[0][::-1,:,:].transpose((1,2,0)))

B = B[:,::-1,:,:]

bb = scipy.misc.imresize(B[0],(128,128),'cubic','RGB')
plt.imshow(bb)

bb = scipy.misc.imresize(B[0],(64,64),'cubic','RGB')
plt.imshow(bb)

ndata = 0
imgsize = 64
# TODO: Handle multiple hdf5 files, need to expand data or
# batch process (fitting, really) one file at a time
for dfile in dfiles:
    with h5py.File(dfile,'r') as h5f:
        # raw data
        A = dict(h5f.items()) 
        # extract images in 1-byte format
        B = np.array(A['images'].value,dtype=np.uint8)
        # change BGR to RGB
        B = B[:,::-1,:,:]
        # Scale down image size
        imgs = np.zeros((len(B),3,64,64),dtype=np.uint8)
        for i,b in enumerate(B):
            imgs[i] = scipy.misc.imresize(b,(64,64),'cubic','RGB').transpose((2,0,1))
        # speed and accel
        speedx = A['vehicle_states'].value[:,2:4]
        # throttle and steering
        targets = A['targets'].value[:,4:]


# frame size
nrows = 64
ncols = 64

# accel, speed, distance, angle
real_in = Input(shape=(2,), name='real_input')

# video frame in, grayscale
frame_in = Input(shape=(3,nrows,ncols))

# convolution for image input
conv = Convolution2D(4,5,5,border_mode='same',
        activation='relu')
conv_l = conv(frame_in)
pool_l = MaxPooling2D(pool_size=(2,2))(conv_l)

flat = Flatten()(pool_l)

M = merge([flat,real_in], mode='concat', concat_axis=1)

Accel = Dense(1, activation='linear')(M)
Steer = Dense(1, activation='linear')(M)

model = Model(input=[real_in, frame_in], output=[Accel,Steer])

model.compile(loss='mean_squared_error',
              optimizer='rmsprop',
              metrics=['accuracy'])

#nsamples = 1000
#fake_real = np.random.random((nsamples,4))
#fake_frame = np.random.random((nsamples,1,nrows,ncols))

#fake_A = np.random.random(nsamples)
#fake_P = np.random.random(nsamples)

h = model.fit([speedx, imgs], [targets[:,0], targets[:,1]], batch_size = 32, nb_epoch=10, verbose=1)

W = model.get_weights()

# look at conv filters separately in color channel
f, con = plt.subplots(4,3, sharex='col', sharey='row')
for row in range(4):
    for col in range(3):
        con[row,col].pcolormesh(W[0][row,col],cmap=plt.cm.hot)


# combine color channels into on filter image
f, con = plt.subplots(4,1, sharex='col', sharey='row')
for row in range(4):
    con[row].imshow(W[0][row].transpose((1,2,0)),
                    interpolation="none")


