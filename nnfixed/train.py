import os 
import math
import numpy as np
import glob
import datetime
import argparse

import keras
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten, Reshape
from keras.layers import Embedding, Input, merge
from keras.layers.convolutional import Conv2D, MaxPooling2D
from keras.optimizers import Adam
from keras.regularizers import l2, l1
from keras.utils.np_utils import to_categorical
from keras import backend as K

#This code sets up the parser for command line arguments specifying parameters for training.
parser=argparse.ArgumentParser()
parser.add_argument('--weight_filename', action='store', default='weights', help='prefix for saved weight files')
parser.add_argument('--init_weights', action='store', default='', 
        help='specifies an existing weight file to use as an initial condition for the network at the start of training')
parser.add_argument('--delay', action='store', default=0, type=int, 
        help='delay between image and steering training data to compensate for processing delay during runtime')
parser.add_argument('--epochs', action='store', default=100, type=int, 
        help='number of epochs to train over')
parser.add_argument('--save_frequency', action='store', default=10, type=int, 
        help='number of epochs between weight file saves')
parser.add_argument('directories', nargs='+', help='list of directories to read training data from')

args=parser.parse_args()

args.directories.sort() #sort directories once, so they will be in the same order when we read images and commands
time_format='%Y-%m-%d_%H-%M-%S'
trainstart=datetime.datetime.now()
time_string=trainstart.strftime(time_format)

steer=np.array([]) #this is where we store the steering training data
data_lengths=[] #this will hold the lengths of each file of steering data after zeros are trimmed.
#this loops through the input directories, and then through the files in the directories to load in the steering data:
for directory in args.directories:
    ctlfiles=glob.glob(os.path.join(directory, 'commands*.npz'))
    for ctlfile in sorted(ctlfiles):
        ctldata=np.load(ctlfile)['arr_0']
        data_to_append=np.trim_zeros(ctldata[:, 0], trim='b')
        data_lengths.append(len(data_to_append))
        steer=np.concatenate((steer, data_to_append[args.delay:len(data_to_append)]), axis=0)#note that we compensate for delay here

#use these values to normalize target data before training
steerSampleMean=steer.mean()
steerSampleSTD=steer.std()
#these values get saved to un-normalize network output during testing
np.savez("steerstats.npz", [steerSampleMean, steerSampleSTD])

#defines image size:
nrows=78
ncols=128

#total number of image/output training pairs, calculated from number of non-zero steering values
total_training_samples=sum(data_lengths) 
#note that we compensate for delay here:
training_images=np.zeros((total_training_samples-args.delay*len(data_lengths), nrows, ncols, 3)).astype('float32')

i=0
n=0
#this loops through the input directories, then through the files in each directory, then through the images in each file
#   to load the images into the image array:
for directory in args.directories:
    imgfiles=glob.glob(os.path.join(directory, 'imgs*.npz'))
    for imgfile in sorted(imgfiles):
        imdata=np.load(imgfile)['arr_0'].astype('float32')
        for image in imdata[0:data_lengths[i]-args.delay]: #note that we compensate for delay here
            crop_image=image[0:nrows, :]
            #we have to normalize each image to zero mean, unit variance:
            image_mean=crop_image.mean()
            image_std=crop_image.std()
            training_images[n]=(crop_image-image_mean)/image_std
            n+=1#this increments for each image, and keeps track of where to put the images in the training_images array
        i+=1#this increments for each file, and keeps track of where to get the number of data frames from data_lengths


#this loads the predefined network architecture from dropout_model.py
from dropout_model import model
num_epochs=args.epochs#number of epochs to train over
save_epochs=args.save_frequency#number of epochs between weight file saves
#if the user inputs a weight file for initial state, load it:
if args.init_weights!="":
    model.load_weights(args.init_weights)

for n in range(num_epochs):
    print("starting epoch {0}".format(n))
    h=model.fit([training_images], [(steer-steerSampleMean)/steerSampleSTD], 
                batch_size=25, epochs=1, verbose=1, validation_split=0.1, shuffle=True)

    if n%save_epochs ==0 :
        savename='%s_%s_epoch_%d.h5'%(args.weight_filename, time_string, n)
        print("Saving epoch {0} to {1}".format(n, savename))
        model.save_weights(savename, overwrite=True)

savename='%s_%s_complete.h5'%(args.weight_filename, timestring)
model.save_weights(savename, overwrite=True)
