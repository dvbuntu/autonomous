import os
import math
import numpy as np
import h5py
import glob
from tqdm import tqdm
import scipy

import keras
from keras.utils.np_utils import to_categorical
import sklearn.metrics as metrics
import keras.utils.np_utils

from PIL import Image, ImageDraw

import matplotlib.pyplot as plt
plt.ion()


ndata = 0
imgsize = 64
# frame size
nrows = 64
ncols = 64

# His model
import keras.layers

model_a = keras.models.Sequential()
model_a.add(keras.layers.Dropout(0.0, input_shape=(1, nrows,ncols)))
model_a.add(keras.layers.Convolution2D(32,3,3,border_mode='same'))
model_a.add(keras.layers.Activation('relu'))
model_a.add(keras.layers.MaxPooling2D(pool_size=(2,2)))
model_a.add(keras.layers.Convolution2D(64,3,3,border_mode='same', activation='relu'))
model_a.add(keras.layers.MaxPooling2D(pool_size=(2,2)))
model_a.add(keras.layers.Flatten())

model_b = keras.models.Sequential()
model_b.add(keras.layers.InputLayer((2,)))


model = keras.models.Sequential()
model.add(keras.layers.Merge([model_a, model_b], mode = 'concat', concat_axis=1))
model.add(keras.layers.Dense(128, activation='relu'))
model.add(keras.layers.Dense(32, activation = 'relu'))
model.add(keras.layers.Dense(1, activation ='linear'))

adam = keras.optimizers.Adam(lr=0.001)

model.compile(loss='mean_squared_error',
              optimizer=adam,
              metrics=['mse'])



imgs = np.load('data/imgs_arr_big.npz')['arr_0']
speedx = np.load('data/speedx_arr_big.npz')['arr_0']
targets = np.load('data/targets_arr_big.npz')['arr_0']


# SHuffle data
idx = np.arange(0,imgs.shape[0])
idx = np.random.permutation(idx)
imgs = imgs[idx,:,:,:]
speedx = speedx[idx,:]
targets = targets[idx,:]

# make targets grayscale
imgsGray = np.mean(imgs, axis=1)
imgsGray = imgsGray[:,None,:,:]



h = model.fit([imgsGray, speedx], [targets[:,0]],
              batch_size = 32, nb_epoch=10, verbose=1,
              validation_split=0.1, shuffle=True)

preds = model.predict([imgsGray, speedx])
steer_preds = preds.reshape([-1])
plt.plot(np.array([steer_preds.reshape(len(steer_preds)),targets[:,0]]).T,'.')

# Animation!
def get_point(s,start=0,end=63,height= 16):
    X = int(s*(end-start))
    if X < start:
        X = start
    if X > end:
        X = end
    return (X,height)

val_idx = 0

import matplotlib.animation as animation
figure = plt.figure()
imageplot = plt.imshow(np.zeros((64, 64, 3), dtype=np.uint8))
def next_frame(i):
    im = Image.fromarray(np.array(imgs[val_idx+i].transpose(1,2,0),dtype=np.uint8))
    p = get_point(1-steer_preds[i])
    t = get_point(1-targets[i+val_idx,0])
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

