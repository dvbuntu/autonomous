import math
import numpy as np

import keras
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten, Reshape
from keras.layers import Embedding, Input, merge
from keras.layers.convolutional import Conv2D, MaxPooling2D
from keras.optimizers import Adam, SGD
from keras.regularizers import l2, l1
from keras.utils.np_utils import to_categorical
from keras.layers.normalization import BatchNormalization
from keras import backend as K


nrows=36
ncols=128
wr=0.00001 # l1 regularizer value
dp=0.125 # dropout rate 

# Note: Dan used the keras functional paradigm to define his network.
# I'm using the sequential paradigm. 
model=Sequential()
frame_in = Input(shape=(3, nrows, ncols), name='img_input')

#we should do a local contrast normalization

#5x5 convolutional layer with a stride of 2
model.add(BatchNormalization(input_shape=(nrows, ncols, 3)))
model.add(Conv2D(24, (5, 5), activation='elu', padding='same', kernel_initializer='lecun_uniform'))
model.add(MaxPooling2D(pool_size=(2, 2), data_format="channels_last"))
model.add(Dropout(dp))

#5x5 convolutional layer with a stride of 2
model.add(BatchNormalization())
model.add(Conv2D(32, (5, 5), activation='elu', padding='same', kernel_initializer='lecun_uniform'))
model.add(MaxPooling2D(pool_size=(2, 2), data_format="channels_last"))
model.add(Dropout(dp))


#5x5 convolutional layer with a stride of 2
model.add(BatchNormalization())
model.add(Conv2D(40, (5, 5), activation='elu', padding='same', kernel_initializer='lecun_uniform'))
model.add(MaxPooling2D(pool_size=(2, 2), data_format="channels_last"))
model.add(Dropout(dp))


#3x3 convolutional layer with no stride 
model.add(BatchNormalization())
model.add(Conv2D(48, (3, 3), activation='elu', padding='same', kernel_initializer='lecun_uniform'))
model.add(MaxPooling2D(pool_size=(2, 2), data_format="channels_last"))
model.add(Dropout(dp))


#3x3 convolutional layer with no stride 
model.add(BatchNormalization())
model.add(Conv2D(48, (3, 3), activation='elu', padding='same', kernel_initializer='lecun_uniform'))
model.add(MaxPooling2D(pool_size=(2, 2), data_format="channels_last"))
model.add(BatchNormalization())
model.add(Dropout(dp))


model.add(Flatten())

#fully connected layer
model.add(Dense(100, activation='elu', kernel_initializer='lecun_uniform'))
#model.add(Dropout(dp))

#fully connected layer to output node
model.add(Dense(1, activation='linear', kernel_initializer='lecun_uniform'))

model.compile(loss=['mse'], optimizer=SGD(lr=0.001, decay=1e-6, momentum=0.9, nesterov=True), metrics=['mse'])
print(model)
