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
from keras.layers.recurrent import SimpleRNN, LSTM
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.layers.recurrent import SimpleRNN, LSTM
from keras.optimizers import SGD, Adam, RMSprop
from keras.regularizers import l2, activity_l2, l1
from keras.utils.np_utils import to_categorical
from keras import backend as K
import sklearn.metrics as metrics

from PIL import Image, ImageDraw

import matplotlib.pyplot as plt
plt.ion()


ndata = 0
imgsize = 64
# frame size
nrows = 64
ncols = 64
wr = 0.00000
dp = 0.0

# speed, accel, distance, angle
real_in = Input(shape=(2,), name='real_input')

# video frame in, grayscale
frame_in = Input(shape=(3,nrows,ncols), name='img_input')

# convolution for image input
conv1 = Convolution2D(24,5,5,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform')
conv_l1 = conv1(frame_in)
Econv_l1 = ELU()(conv_l1)
pool_l1 = MaxPooling2D(pool_size=(2,2))(Econv_l1)
drop_l1 = Dropout(dp)(pool_l1)

conv2 = Convolution2D(32,5,5,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform')
conv_l2 = conv2(drop_l1)
Econv_l2 = ELU()(conv_l2)
pool_l2 = MaxPooling2D(pool_size=(2,2))(Econv_l2)
drop_l2 = Dropout(dp)(pool_l2)

conv3 = Convolution2D(40,5,5,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform')
conv_l3 = conv3(drop_l2)
Econv_l3 = ELU()(conv_l3)
pool_l3 = MaxPooling2D(pool_size=(2,2))(Econv_l3)
drop_l3 = Dropout(dp)(pool_l3)

conv4 = Convolution2D(48,5,5,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform')
conv_l4 = conv4(drop_l3)
Econv_l4 = ELU()(conv_l4)
pool_l4 = MaxPooling2D(pool_size=(2,2))(Econv_l4)
drop_l4 = Dropout(dp)(pool_l4)

conv5 = Convolution2D(64,5,5,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform')
conv_l5 = conv5(drop_l4)
Econv_l5 = ELU()(conv_l5)
pool_l5 = MaxPooling2D(pool_size=(2,2))(Econv_l5)
drop_l5 = Dropout(dp)(pool_l5)

flat = Flatten()(drop_l5)

M = merge([flat,real_in], mode='concat', concat_axis=1)
Rs = Reshape((1,256+2))(M)

R = SimpleRNN(64)(Rs)

#R = Reshape((num_blocks,num_features))(M)
#L = LSTM(output_dim=256, activation='sigmoid', inner_activation='hard_sigmoid')(R)

D1 = Dense(64,W_regularizer=l1(wr), init='lecun_uniform')(R)
ED1 = ELU()(D1)
DED1 = Dropout(dp)(ED1)

S1 = Dense(64,W_regularizer=l1(wr), init='lecun_uniform')(DED1)
ES1 = ELU()(S1)

#Steer_node = Dense(1, name='steer_node', init='lecun_uniform')(ES1)
#Steer_out = Activation(clamp,name='steer_out')(Steer_node)
Steer_out = Dense(1, activation='linear', name='steer_out', init='lecun_uniform')(ES1)

model = Model(input=[real_in, frame_in], output=[Steer_out])

sgd = SGD(lr=0.003)
adam = Adam(lr=0.01)


model.compile(loss=['mse'],
              optimizer=adam,
              metrics=['mse'])





imgs = np.load('data/imgs_arr_2.npz')['arr_0']
speedx = np.load('data/speedx_arr_2.npz')['arr_0']
targets = np.load('data/targets_arr_2.npz')['arr_0']


nb_epoch = 100
mini_epoch = 5
num_steps = int(nb_epoch/mini_epoch)


h = model.fit([speedx, imgs], {'steer_out':targets[:,0]},
                batch_size = 32, nb_epoch=1, verbose=1,
                validation_split=0.1, shuffle=False)


for step in tqdm(range(0,num_steps)):
    h = model.fit([speedx, imgs], {'steer_out':targets[:,0]},
                    batch_size = 32, nb_epoch=mini_epoch, verbose=1,
                    validation_split=0.1, shuffle=False)
    model.save_weights('steer_nodrop_l2_big2_RNN_fixed_{0}_{1:4.5}.h5'.format(step,h.history['val_loss'][-1]),overwrite=True)


from keras.layers.wrappers import TimeDistributed

n_timesteps = 4

# speed, accel, distance, angle
real_in = Input(shape=(2,), name='real_input')

# video frame in, grayscale
frame_in = Input(shape=(3,nrows,ncols), name='img_input')

# convolution for image input
conv1 = Convolution2D(24,5,5,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform')
conv_l1 = conv1(frame_in)
Econv_l1 = ELU()(conv_l1)
pool_l1 = MaxPooling2D(pool_size=(2,2))(Econv_l1)
drop_l1 = Dropout(dp)(pool_l1)

conv2 = Convolution2D(32,5,5,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform')
conv_l2 = conv2(drop_l1)
Econv_l2 = ELU()(conv_l2)
pool_l2 = MaxPooling2D(pool_size=(2,2))(Econv_l2)
drop_l2 = Dropout(dp)(pool_l2)

conv3 = Convolution2D(40,5,5,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform')
conv_l3 = conv3(drop_l2)
Econv_l3 = ELU()(conv_l3)
pool_l3 = MaxPooling2D(pool_size=(2,2))(Econv_l3)
drop_l3 = Dropout(dp)(pool_l3)

conv4 = Convolution2D(48,5,5,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform')
conv_l4 = conv4(drop_l3)
Econv_l4 = ELU()(conv_l4)
pool_l4 = MaxPooling2D(pool_size=(2,2))(Econv_l4)
drop_l4 = Dropout(dp)(pool_l4)

conv5 = Convolution2D(64,5,5,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform')
conv_l5 = conv5(drop_l4)
Econv_l5 = ELU()(conv_l5)
pool_l5 = MaxPooling2D(pool_size=(2,2))(Econv_l5)
drop_l5 = Dropout(dp)(pool_l5)

flat = Flatten()(drop_l5)

M = merge([flat,real_in], mode='concat', concat_axis=1)

Rs = Reshape((1,256+2))(M)
L = LSTM(output_dim=64, activation='sigmoid', inner_activation='hard_sigmoid', return_sequences = True)(Rs)

flatL = Flatten()(L)

D1 = Dense(64,W_regularizer=l1(wr), init='lecun_uniform')(flatL)
ED1 = ELU()(D1)
DED1 = Dropout(dp)(ED1)

S1 = Dense(64,W_regularizer=l1(wr), init='lecun_uniform')(DED1)
ES1 = ELU()(S1)

#Steer_node = Dense(1, name='steer_node', init='lecun_uniform')(ES1)
#Steer_out = Activation(clamp,name='steer_out')(Steer_node)
Steer_out = Dense(1, activation='linear', name='steer_out', init='lecun_uniform')(ES1)

model = Model(input=[real_in, frame_in], output=[Steer_out])

sgd = SGD(lr=0.003)
adam = Adam(lr=0.01)


model.compile(loss=['mse'],
              optimizer=adam,
              metrics=['mse'])


