import os
import glob
import cv2
import numpy as np

imagefiles=glob.glob(os.path.join('data', 'imgs*.npz'))
numfiles=len(imagefiles)
print(numfiles)

#images=np.zeros((100*numfiles, 96, 128, 3))

imdata=np.array((100, 96, 128, 3))
i=0
l=[]
for imagefile in sorted(imagefiles):
    imdata=np.load(imagefile)['arr_0']
    j=0
    numempty=0
    for im in imdata:
        #images[i*100+j]=im
        j=j+1
        imsum=np.sum(im)
        if imsum==0:
            numempty=numempty+1
    l.append(numempty)

#print(images.shape)
for f, n in zip(sorted(imagefiles), l):
    print("{0} : {1}".format(f, n))
