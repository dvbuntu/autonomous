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
from keras.optimizers import SGD, Adam, RMSprop
from keras.regularizers import l2, activity_l2
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

# speed, accel, distance, angle
real_in = Input(shape=(2,), name='real_input')

# video frame in, grayscale
frame_in = Input(shape=(3,nrows,ncols))

# convolution for image input
conv1 = Convolution2D(4,5,5,border_mode='same', W_regularizer=l2(0.001))
conv_l1 = conv1(frame_in)
Econv_l1 = ELU()(conv_l1)
pool_l1 = MaxPooling2D(pool_size=(2,2))(Econv_l1)

conv2 = Convolution2D(8,4,4,border_mode='same', W_regularizer=l2(0.001))
conv_l2 = conv2(pool_l1)
Econv_l2 = ELU()(conv_l2)
pool_l2 = MaxPooling2D(pool_size=(2,2))(Econv_l2)

conv3 = Convolution2D(16,3,3,border_mode='same', W_regularizer=l2(0.001))
conv_l3 = conv3(pool_l2)
Econv_l3 = ELU()(conv_l3)
pool_l3 = MaxPooling2D(pool_size=(2,2))(Econv_l3)

flat = Flatten()(pool_l3)

M = merge([flat,real_in], mode='concat', concat_axis=1)

D1 = Dense(64,W_regularizer=l2(0.001))(M)
ED1 = ELU()(D1)
D2 = Dense(32,W_regularizer=l2(0.001))(ED1)
ED2 = ELU()(D2)
D3 = Dense(32,W_regularizer=l2(0.001))(ED2)
ED3 = ELU()(D3)

S1 = Dense(32,W_regularizer=l2(0.001))(ED3)
ES1 = ELU()(S1)
S2 = Dense(32,W_regularizer=l2(0.001))(S1)
ES2 = ELU()(S2)
S3 = Dense(32,W_regularizer=l2(0.001))(S2)
ES3 = ELU()(S3)

Steer = Dense(1, activation='linear',W_regularizer=l2(0.001))(ES3)

G1 = Dense(32,W_regularizer=l2(0.001))(ED3)
EG1 = ELU()(G1)
G2 = Dense(32,W_regularizer=l2(0.001))(G1)
EG2 = ELU()(G2)
G3 = Dense(32,W_regularizer=l2(0.001))(G2)
EG3 = ELU()(G3)

Accel = Dense(3, activation='sigmoid')(EG3)

model = Model(input=[real_in, frame_in], output=[Steer,Accel])

adam = Adam(lr=0.001)

model.compile(loss=['mean_squared_error',
                    'categorical_crossentropy'],
              optimizer=adam,
              metrics=['mse','accuracy'])

# Switch to the compressed data input
# Huzzah!

imgs = np.load('data/imgs_arr_big.npz')['arr_0']
speedx = np.load('data/speedx_arr_big.npz')['arr_0']
targets = np.load('data/targets_arr_big.npz')['arr_0']
gas_target = to_categorical(targets[:,1])
nb_epoch = 10000
mini_epoch = 10
num_steps = int(nb_epoch/mini_epoch)
for step in tqdm(range(num_steps)):
    h = model.fit([speedx, imgs], [targets[:,0],gas_target],
                    batch_size = 32, nb_epoch=mini_epoch, verbose=1,
                    validation_split=0.1, shuffle=True)
    model.save_weights('steer_simple_l2_big_{0}_{1:4.5}.h5'.format(step,h.history['loss'][-1]),overwrite=True)

model.save_weights('steer_simple_l2_big_final.h5',overwrite=True)
model.load_weights('steer_simple_l2_big_final.h5')

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

preds = model.predict([speedx,imgs])
steer_preds = preds[0].reshape([-1])
gas_preds = np.argmax(preds[1],axis=1)

#FYI 1.0 is to the left, 0. is to the right
# unless I'm mixing up my directions in the animation


# plot predictions and actual
plt.plot(np.array([steer_preds.reshape(len(steer_preds)),targets[:,0]]).T,'.')
plt.plot(steer_preds.reshape(len(steer_preds)),targets[:,0],'.')

# Animation!
def get_point(s,start=0,end=63,height= 16):
    X = int(s*(end-start))
    if X < start:
        X = start
    if X > end:
        X = end
    return (X,height)

import matplotlib.animation as animation
figure = plt.figure()
imageplot = plt.imshow(np.zeros((64, 64, 3), dtype=np.uint8))
def next_frame(i):
    im = Image.fromarray(np.array(imgs[i].transpose(1,2,0),dtype=np.uint8))
    p = get_point(1-steer_preds[i])
    t = get_point(1-targets[i,0])
    draw = ImageDraw.Draw(im) 
    draw.line((32,63, p,p),
                fill=(255,0,0,128))
    draw.line((32,63, t,t),
                fill=(0,255,0,128))
    imageplot.set_array(im)
    #if i % 10 == 0:
    #    print(i)
    return imageplot,
animate = animation.FuncAnimation(figure, next_frame, frames=range(0,len(imgs)), interval=25, blit=False)
plt.show()


