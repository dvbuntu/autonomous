import os 
import math
import numpy as np
import glob

import keras
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten, Reshape
from keras.layers import Embedding, Input, merge
from keras.layers.convolutional import Conv2D, MaxPooling2D
from keras.optimizers import Adam
from keras.regularizers import l2, l1
from keras.utils.np_utils import to_categorical
from keras import backend as K


nrows=96
ncols=128

num_epochs=100
save_epochs=10
weightfile='weights.h5'
data_dir='datafiles'

ctlfiles=glob.glob(os.path.join(data_dir, 'commands*.npz'))
steer=np.array([])
for ctlfile in sorted(ctlfiles):
  ctldata=np.load(ctlfile)['arr_0']
  steer=np.concatenate((steer, np.trim_zeros(ctldata[:, 0], trim='b')), axis=0)

#use these values to normalize target data before training
steerSampleMean=steer.mean()
steerSampleSTD=steer.std()

from testmodel import model

img_files=glob.glob(os.path.join(data_dir, 'imgs*.npz'))
command_files=glob.glob(os.path.join(data_dir, 'commands*.npz'))

for n in range(num_epochs):
    print("starting epoch {0}".format(n))
    for i,c in zip(sorted(img_files), sorted(command_files)):
        print(i, c)
        imgs=np.load(i)['arr_0']
        commands=np.load(c)['arr_0']
        h=model.fit([imgs], [(commands[:, 0]-steerSampleMean)/steerSampleSTD], 
                batch_size=5, epochs=1, verbose=1, validation_split=0.1, shuffle=True)

    if n%save_epochs ==0 :
        print("Saving epoch {0} to {1}".format(n, weightfile))
        model.save_weights(weightfile, overwrite=True)

model.save_weights(weightfile, overwrite=True)
