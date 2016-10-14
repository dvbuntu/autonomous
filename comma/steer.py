import h5py
import scipy
import scipy.misc
import glob
import numpy as np
from tqdm import tqdm

import matplotlib.pyplot as plt
plt.ion()

# Grab the model
from model import model

# Read subset of data
all_data = np.load('simple_data.npz')
imgs_color = all_data['imgs']
speedx = np.concatenate((all_data['spds'], all_data['accel']))
speedx = speedx.reshape((-1,2))
steer = all_data['steer']

# make targets grayscale
imgs = np.mean(imgs_color, axis=1)
imgs = imgsGray[:,None,:,:]


# Train a little bit
nb_epoch = 100
mini_epoch = 10
num_steps = int(nb_epoch/mini_epoch)
for step in tqdm(range(0,num_steps)):
    h = model.fit([speedx, imgs], {'steer_out':steer},
                    batch_size = 32, nb_epoch=mini_epoch, verbose=1,
                    validation_split=0.1, shuffle=True)
    model.save_weights('steer_comma_{0}_{1:4.5}.h5'.format(step,h.history['val_loss'][-1]),overwrite=True)

# Make predictions
start = 25000
stop = 27000
preds = model.predict([speedx[start:stop],imgs[start:stop]])
steer_preds = preds.reshape([-1])

# Animation!
def get_point(s,start=0,end=63,height= 16):
    X = int(s*(end-start))
    if X < start:
        X = start
    if X > end:
        X = end
    return (X,height)


# Video of prediction
import matplotlib.animation as animation
from PIL import Image, ImageDraw
figure = plt.figure()
imageplot = plt.imshow(np.zeros((64, 64, 3), dtype=np.uint8))
val_idx = start
def next_frame(i):
    im = Image.fromarray(np.array(imgs[val_idx+i].transpose(1,2,0),dtype=np.uint8))
    p = get_point(steer_preds[i])
    t = get_point(steer[i+val_idx])
    draw = ImageDraw.Draw(im) 
    draw.line((32,63, p,p),
                fill=(255,0,0,128))
    draw.line((32,63, t,t),
                fill=(0,255,0,128))
    imageplot.set_array(im)
    return imageplot,
animate = animation.FuncAnimation(figure, next_frame, frames=range(0,stop-start), interval=25, blit=False)
plt.show()


