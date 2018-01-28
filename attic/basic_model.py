import os
import math
import numpy as np
import h5py
from tqdm import tqdm

import keras
from keras.models import Sequential, Model
from keras.layers.core import Dense, Dropout, Activation, Flatten, Reshape
from keras.layers import Embedding, Input, merge
from keras.layers.recurrent import SimpleRNN, LSTM
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.optimizers import SGD, Adam, RMSprop
import sklearn.metrics as metrics

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
