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
from keras.layers import Embedding, Input, merge, ELU
from keras.layers import Concatenate
from keras.layers import concatenate
from keras.layers.recurrent import SimpleRNN, LSTM
from keras.layers.convolutional import Conv2D, MaxPooling2D
from keras.optimizers import SGD, Adam, RMSprop
from keras.regularizers import l2, l1
from keras.utils.np_utils import to_categorical
from keras import backend as K
import sklearn.metrics as metrics

ndata = 0
imgsize = 64
# frame size
nrows = 64
ncols = 64
wr = 0.00001
dp = 0.125

# speed, accel, distance, angle
real_in = Input(shape=(2,), name='real_input')

# video frame in, grayscale
frame_in = Input(shape=(3,nrows,ncols), name='img_input')

# convolution for image input
conv1 = Conv2D(24,(5,5), padding='same', kernel_regularizer=l1(wr), kernel_initializer='lecun_uniform')
conv_l1 = conv1(frame_in)
Econv_l1 = ELU()(conv_l1)
pool_l1 = MaxPooling2D(pool_size=(2,2))(Econv_l1)

conv2 = Conv2D(32,(5,5),padding='same', kernel_regularizer=l1(wr), kernel_initializer='lecun_uniform')
conv_l2 = conv2(pool_l1)
Econv_l2 = ELU()(conv_l2)
pool_l2 = MaxPooling2D(data_format="channels_first", pool_size=(2,2))(Econv_l2)
drop_l2 = Dropout(dp)(pool_l2)

conv3 = Conv2D(40,(5,5),padding='same', kernel_regularizer=l1(wr), kernel_initializer='lecun_uniform')
conv_l3 = conv3(drop_l2)
Econv_l3 = ELU()(conv_l3)
pool_l3 = MaxPooling2D(data_format="channels_first", pool_size=(2,2))(Econv_l3)
drop_l3 = Dropout(dp)(pool_l3)

conv4 = Conv2D(48,(5,5),padding='same', kernel_regularizer=l1(wr), kernel_initializer='lecun_uniform')
conv_l4 = conv4(drop_l3)
Econv_l4 = ELU()(conv_l4)
pool_l4 = MaxPooling2D(data_format="channels_first", pool_size=(2,2))(Econv_l4)
drop_l4 = Dropout(dp)(pool_l4)

conv5 = Conv2D(64,(5,5),padding='same', kernel_regularizer=l1(wr), kernel_initializer='lecun_uniform')
conv_l5 = conv5(drop_l4)
Econv_l5 = ELU()(conv_l5)
pool_l5 = MaxPooling2D(data_format="channels_first", pool_size=(2,2))(Econv_l5)
drop_l5 = Dropout(dp)(pool_l5)

flat = Flatten()(drop_l5)

M = concatenate([flat,real_in], axis=-1)

D1 = Dense(256,kernel_regularizer=l1(wr), kernel_initializer='lecun_uniform')(M)
ED1 = ELU()(D1)
DED1 = Dropout(dp)(ED1)

D2 = Dense(128,kernel_regularizer=l1(wr), kernel_initializer='lecun_uniform')(DED1)
ED2 = ELU()(D2)
DED2 = Dropout(dp)(ED2)

D3 = Dense(128,kernel_regularizer=l1(wr), kernel_initializer='lecun_uniform')(DED2)
ED3 = ELU()(D3)
DED3 = Dropout(dp)(ED3)

S1 = Dense(64,kernel_regularizer=l1(wr), kernel_initializer='lecun_uniform')(DED3)
ES1 = ELU()(S1)

#Steer_node = Dense(1, name='steer_node', kernel_initializer='lecun_uniform')(ES1)
#Steer_out = Activation(clamp,name='steer_out')(Steer_node)
Steer_out = Dense(1, activation='linear', name='steer_out', kernel_initializer='lecun_uniform')(ES1)

model = Model(inputs=[real_in, frame_in], outputs=[Steer_out])

sgd = SGD(lr=0.003)
adam = Adam(lr=0.001)


model.compile(loss=['mse'],
              optimizer=adam,
              metrics=['mse'])


