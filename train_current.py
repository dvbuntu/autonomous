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
from keras.regularizers import l2, l1
from keras.utils.np_utils import to_categorical
from keras import backend as K
import sklearn.metrics as metrics

import argparse


parser = argparse.ArgumentParser(description='Train Otto based on collected data.')
parser.add_argument('-n','--num_epochs', action='store', default=100)
parser.add_argument('-s','--save_epochs', action='store', default=10)
parser.add_argument('-d','--debug', action='store_true', default=False)
parser.add_argument('-w','--weights', action='store', default='weights.h5')
parser.add_argument('-f','--data_dir', action='store', default='data')

args = parser.parse_args()
num_epochs = int(args.num_epochs)
save_epochs = int(args.save_epochs)
debug = args.debug
weightfile = args.weights
data_dir = args.data_dir


from current_model import model

# last 10% of every file provides validation...
img_files = glob.glob(os.path.join([data_dir,'imgs*.npz'])) 
speedx_files = glob.glob(os.path.join([data_dir,'speedx*.npz'])) 
target_files = glob.glob(os.path.join([data_dir,'targets*.npz'])) 

# step through each data file, doing an epoch at a time
for n in range(num_epochs):
    print("Starting epoch {0}".format(n))
    for i,s,t in zip(img_files, speedx_files, target_files):
        imgs = np.load(i)['arr_0']
        speedx = np.load(s)['arr_0']
        targets = np.load(t)['arr_0']
        h = model.fit([speedx, imgs], [targets[:,0]],
                        batch_size = 32, nb_epoch=1, verbose=1,
                        validation_split=0.1, shuffle=True)
    if n % save_epochs == 0:
        print("Saving epoch {0} to {1}".format(n,weightfile))
        model.save_weights(weightfile,overwrite=True)

# final weight saving
model.save_weights(weightfile,overwrite=True)


