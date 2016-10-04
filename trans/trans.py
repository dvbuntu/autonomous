from keras.models import Model, model_from_json, Sequential
from keras.layers import Input, merge, AveragePooling2D
from keras.layers.convolutional import Convolution2D, MaxPooling2D, ZeroPadding2D
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.regularizers import l2, activity_l2, l1
import sklearn.metrics as metrics
from keras.utils.np_utils import to_categorical
from keras.optimizers import SGD, Adam, RMSprop
from keras.layers import Embedding, Input, merge, ELU
from keras.layers import Embedding, Input, merge, ELU

ndata = 0
# frame size
nrows = 64
ncols = 64
wr = 0.00001
dp = 0.


# Modular function for Fire Node

def fire_module(x, squeeze=16, expand=64):
    x = Convolution2D(squeeze, 1, 1, border_mode='valid')(x)
    x = Activation('relu')(x)

    left = Convolution2D(expand, 1, 1, border_mode='valid')(x)
    left = Activation('relu')(left)

    right= ZeroPadding2D(padding=(1, 1))(x)
    right = Convolution2D(expand, 3, 3, border_mode='valid')(right)
    right = Activation('relu')(right)

    y = merge([left, right], mode='concat', concat_axis=1)
    return y


# Original SqueezeNet from paper. Global Average Pool implemented manually with Average Pooling Layer

def get_squeezenet_trans( img_size = (64,64)):
    input_img = Input(shape=(3, img_size[0], img_size[1]))
    x = Convolution2D(96, 7, 7, subsample=(2, 2), border_mode='valid')(input_img)
    x = Activation('relu')(x)
    x = MaxPooling2D(pool_size=(3, 3), strides=(2, 2))(x)

    x = fire_module(x, 16, 64)
    x = fire_module(x, 16, 64)
    x = fire_module(x, 32, 128)
    x = MaxPooling2D(pool_size=(3, 3), strides=(2, 2))(x)

    x = fire_module(x, 32, 128)
    x = fire_module(x, 48, 192)
    x = fire_module(x, 48, 192)
    x = fire_module(x, 64, 256)
    x = MaxPooling2D(pool_size=(3, 3), strides=(2, 2))(x)

    x = fire_module(x, 64, 256)
    x = Dropout(0.5)(x)

    x = ZeroPadding2D(padding=(1, 1))(x)

    # Otto takes over
    # speed, accel, distance, angle
    real_in = Input(shape=(2,), name='real_input')

    flat = Flatten()(x)
    M = merge([flat,real_in], mode='concat', concat_axis=1)
    D1 = Dense(32,W_regularizer=l1(wr), init='lecun_uniform')(M)
    ED1 = ELU()(D1)
    DED1 = Dropout(dp)(ED1)

    S1 = Dense(64,W_regularizer=l1(wr), init='lecun_uniform')(DED1)
    ES1 = ELU()(S1)

    Steer_out = Dense(1, activation='linear', name='steer_out', init='lecun_uniform')(ES1)

    model = Model(input=[real_in, input_img], output=[Steer_out])
    adam = Adam(lr=0.001)
    model.compile(loss=['mse'],
                  optimizer=adam,
                  metrics=['mse'])
    return model

def get_squeezenet_mini_trans( img_size = (64,64)):
    input_img = Input(shape=(3, img_size[0], img_size[1]))
    x = Convolution2D(96, 7, 7, subsample=(2, 2), border_mode='valid')(input_img)
    x = Activation('relu')(x)
    x = MaxPooling2D(pool_size=(3, 3), strides=(2, 2))(x)

    x = fire_module(x, 16, 64)
    x = fire_module(x, 16, 64)
    x = fire_module(x, 32, 128)
    x = MaxPooling2D(pool_size=(3, 3), strides=(2, 2))(x)

    # Otto takes over
    # speed, accel, distance, angle
    real_in = Input(shape=(2,), name='real_input')

    flat = Flatten()(x)
    M = merge([flat,real_in], mode='concat', concat_axis=1)
    D1 = Dense(32,W_regularizer=l1(wr), init='lecun_uniform')(M)
    ED1 = ELU()(D1)
    DED1 = Dropout(dp)(ED1)

    S1 = Dense(64,W_regularizer=l1(wr), init='lecun_uniform')(DED1)
    ES1 = ELU()(S1)

    Steer_out = Dense(1, activation='linear', name='steer_out', init='lecun_uniform')(ES1)

    model = Model(input=[real_in, input_img], output=[Steer_out])
    return model


def get_pretrained_squeezenet(model_path, weights_path):

    model = model_from_json(open(model_path).read())
    model.load_weights(weights_path)
    return model

# Want to have input side of model be squeeze net, then another deep layer
M = get_squeezenet_trans((nrows,ncols)) 

import h5py
import numpy as np

model_file = 'sqn_weights.h5'
W = h5py.File(model_file,'r')
np.array(W['graph']['param_0'])
# 52 params
all_w = []
for i in range(52):
    k = 'param_{0}'.format(i)
    all_w.append(np.array(W['graph'][k]))

# Compare shapes
W = M.get_weights()
for i in range(52):
    if W[i].shape != all_w[i].shape:
        print(i,W[i].shape,all_w[i].shape)

M.set_weights(all_w[:-2])

from tqdm import tqdm

imgs = np.load('../data/imgs_arr_big.npz')['arr_0']
speedx = np.load('../data/speedx_arr_big.npz')['arr_0']
targets = np.load('../data/targets_arr_big.npz')['arr_0']
nb_epoch = 100
mini_epoch = 10
num_steps = int(nb_epoch/mini_epoch)
for step in range(0,num_steps):
    h = M.fit([speedx, imgs], {'steer_out':targets[:,0]},
                    batch_size = 32, nb_epoch=mini_epoch, verbose=1,
                    validation_split=0.1, shuffle=True)
    M.save_weights('transfer_{0}_{1:4.5}.h5'.format(step,h.history['val_loss'][-1]),overwrite=True)

#for l in feature_layers:
#    l.trainable = False

M = get_squeezenet_mini_trans((nrows,ncols)) 
adam = Adam(lr=0.001)
M.compile(loss=['mse'],
              optimizer=adam,
              metrics=['mse'])
W = M.get_weights()
for i in range(52):
    if W[i].shape != all_w[i].shape:
        print(i,W[i].shape,all_w[i].shape)

M.set_weights(all_w[:20])
for step in range(0,num_steps):
    h = M.fit([speedx, imgs], {'steer_out':targets[:,0]},
                    batch_size = 32, nb_epoch=mini_epoch, verbose=1,
                    validation_split=0.1, shuffle=True)
    M.save_weights('mini_transfer_{0}_{1:4.5}.h5'.format(step,h.history['val_loss'][-1]),overwrite=True)


