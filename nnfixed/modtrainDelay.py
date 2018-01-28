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


nrows=78
ncols=128

num_epochs=100
save_epochs=10
weightfile='Oct11weights.h5'
data_dir='/home/fubar/otto/autonomous/data/tableOct11'

ctlfiles=glob.glob(os.path.join(data_dir, 'commands*.npz'))
steer=np.array([])
for ctlfile in sorted(ctlfiles):
  ctldata=np.load(ctlfile)['arr_0']
  steer=np.concatenate((steer, np.trim_zeros(ctldata[2:len(ctldata), 0], trim='b')), axis=0)

'''
smSteer=np.zeros(steer.shape)
for i in np.arange(4, len(steer)-5):
    smSteer[i]=np.mean(steer[i-4:i+4])

steer=smSteer[4:-5]
'''

#use these values to normalize target data before training
steerSampleMean=steer.mean()
steerSampleSTD=steer.std()
np.savez("steerstats.npz", [steerSampleMean, steerSampleSTD])
from testmodel import model

img_files=glob.glob(os.path.join(data_dir, 'imgs*.npz'))

imgs=np.zeros((98*len(img_files), 78, 128, 3)).astype('float32')
i=0
for imgfile in sorted(img_files):
    imdata=np.load(imgfile)['arr_0'].astype('float32')
    j=0
    for tim in imdata[0:-2]:
        im=tim[0:78, :]
        immean=im.mean()
        imdev=im.std()
        imgs[i*98+j]=(im-immean)/imdev
        j+=1
    i+=1
#imgs=imgs[4:-5]

for n in range(num_epochs):
    print("starting epoch {0}".format(n))
    h=model.fit([imgs], [(steer-steerSampleMean)/steerSampleSTD], 
                batch_size=25, epochs=1, verbose=1, validation_split=0.1, shuffle=True)

    if n%save_epochs ==0 :
        print("Saving epoch {0} to {1}".format(n, weightfile))
        model.save_weights(weightfile, overwrite=True)

model.save_weights(weightfile, overwrite=True)
