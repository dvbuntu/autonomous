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
from keras.activations import relu
from keras.layers import Embedding, Input, merge, ELU
from keras.layers.recurrent import SimpleRNN, LSTM
from keras.layers.convolutional import Convolution2D, MaxPooling2D, ZeroPadding2D
from keras.optimizers import SGD, Adam, RMSprop
from keras.regularizers import l2, activity_l2, l1
from keras.utils.np_utils import to_categorical
from keras import backend as K
from keras.layers.normalization import BatchNormalization as BN
import sklearn.metrics as metrics

from PIL import Image, ImageDraw

import matplotlib.pyplot as plt
plt.ion()


ndata = 0
imgsize = 227
# frame size
nrows = 227
ncols = 227
wr = 0.00001
dp = 0.

# speed, accel, distance, angle
real_in = Input(shape=(2,), name='real_input')

# Image input
frame_in = Input(shape=(3,nrows,ncols), name='img_input')

# convolution for image input
conv11 = Convolution2D(48,11,11,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform', subsample=[4,4], activation='relu')(frame_in)
pool_l11 = MaxPooling2D(pool_size=(3,3), strides=(2,2))(conv11)

# Weird grouping thing
conv12 = Convolution2D(48,11,11,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform', subsample=[4,4], activation='relu')(frame_in)
pool_l12 = MaxPooling2D(pool_size=(3,3), strides=(2,2))(conv12)

# Group them
grp1 = merge([pool_l11, pool_l12], mode = 'concat', concat_axis=1)

# Normalize...I guess this needs weights?
norm1 = BN()(grp1)


# Next conv layer
conv2 = Convolution2D(256,5,5,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform', activation='relu')(norm1)
pool_l2 = MaxPooling2D(pool_size=(3,3), strides=(2,2))(conv2)
norm2= BN()(pool_l2)

model = Model(input=[frame_in], output=[norm2])




# Borrowed from heuritech
from customlayers import *
inputs = Input(shape=(3,nrows,ncols), name='img_input')
conv_1 = Convolution2D(96, 11, 11,subsample=(4,4),activation='relu',
                       name='conv_1')(inputs)

conv_2 = MaxPooling2D((3, 3), strides=(2,2))(conv_1)
conv_2 = crosschannelnormalization(name="convpool_1")(conv_2)
conv_2 = ZeroPadding2D((2,2))(conv_2)
conv_2 = merge([
    Convolution2D(128,5,5,activation="relu",name='conv_2_'+str(i+1))(
        splittensor(ratio_split=2,id_split=i)(conv_2)
    ) for i in range(2)], mode='concat',concat_axis=1,name="conv_2")

conv_3 = MaxPooling2D((3, 3), strides=(2, 2))(conv_2)
conv_3 = crosschannelnormalization()(conv_3)
conv_3 = ZeroPadding2D((1,1))(conv_3)
conv_3 = Convolution2D(384,3,3,activation='relu',name='conv_3')(conv_3)

conv_4 = ZeroPadding2D((1,1))(conv_3)
conv_4 = merge([
    Convolution2D(192,3,3,activation="relu",name='conv_4_'+str(i+1))(
        splittensor(ratio_split=2,id_split=i)(conv_4)
    ) for i in range(2)], mode='concat',concat_axis=1,name="conv_4")

conv_5 = ZeroPadding2D((1,1))(conv_4)
conv_5 = merge([
    Convolution2D(128,3,3,activation="relu",name='conv_5_'+str(i+1))(
        splittensor(ratio_split=2,id_split=i)(conv_5)
) for i in range(2)], mode='concat',concat_axis=1,name="conv_5")
dense_1 = MaxPooling2D((3, 3), strides=(2,2),name="convpool_5")(conv_5)
dense_1 = Flatten(name="flatten")(dense_1)

#model = Model(input=[inputs], output=[dense_1])
# I think this actually matches, just need to rerig the weights a bit

dense_1 = Dense(4096, activation='relu', name = 'fc6_gtanet')(dense_1)
dense_1 = Dropout(0.5)(dense_1)
dense_2 = Dense(4096, activation='relu', name = 'fc7_gtanet')(dense_1)
dense_2 = Dropout(0.5)(dense_2)
output = Dense(6, activation='linear', name = 'gtanet_fctop')(dense_2)

model = Model(input=[inputs], output=[output])
adam = Adam(lr=0.01)
model.compile(loss=['mse'],
              optimizer=adam,
              metrics=['mse'])

# 227 MB, as advertised
Wm = model.get_weights()

# 1st conv, different axes
Wm[0] = np.transpose(W[0],(3,2,0,1))
Wm[1] = b[0]

# 2nd conv, in groups, I have to assumed they're grouped in a sane way
Wm[2] = np.transpose(W[1][:,:,:,:128],(3,2,0,1))
Wm[3] = b[1][:128]
Wm[4] = np.transpose(W[1][:,:,:,128:],(3,2,0,1))
Wm[5] = b[1][128:]

# 3rd conv, business as usual
Wm[6] = np.transpose(W[2],(3,2,0,1))
Wm[7] = b[2]

# 4th conv, splitsville again
Wm[8] = np.transpose(W[3][:,:,:,:192],(3,2,0,1))
Wm[9] = b[3][:192]
Wm[10] = np.transpose(W[3][:,:,:,192:],(3,2,0,1))
Wm[11] = b[3][192:]

# 5th conv, more splitting
Wm[12] = np.transpose(W[4][:,:,:,:128],(3,2,0,1))
Wm[13] = b[4][:128]
Wm[14] = np.transpose(W[4][:,:,:,128:],(3,2,0,1))
Wm[15] = b[4][128:]

# Dense 1, easy peasy
Wm[16] = W[5]
Wm[17] = b[5]

# Dense 2
Wm[18] = W[6]
Wm[19] = b[6]

# Dense 3, output
Wm[20] = W[7]
Wm[21] = b[7]

np.savez_compressed('deepdrive_wgts.keras.npz',Wm)
Wm = np.load('deepdrive_wgts.keras.npz')['arr_0']

# set the new weights
model.set_weights(Wm)

# grab some example data and upsample
imgs = np.load('../data/imgs_arr.npz')['arr_0']
# Switch back to BGR for caffe style
imgs = imgs[:,::-1,:,:]
speedx = np.load('../data/speedx_arr.npz')['arr_0']
targets = np.load('../data/targets_arr.npz')['arr_0']

import scipy.misc
num = 100
upscaled = np.zeros((num,3,227,227),dtype=np.float32)
for i in range(num):
    upscaled[i] = scipy.misc.imresize(imgs[i],(227,227),'cubic','RGB').transpose((2,0,1))

preds = model.predict([upscaled])
steer_preds = preds[:,5].reshape(num,)
# derp, his steering isn't scaled like mine, his is -1 to 1
plt.plot(np.array([steer_preds.reshape(len(steer_preds)),targets[:num,0]*2-1]).T,'.')

