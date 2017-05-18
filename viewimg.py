import numpy as np
import matplotlib.pyplot as plt
a = np.load("imgs_2017-05-15_22:13:47.npz")
dir(a)
a.keys
a.keys[]
a.keys()
b = a['arr_0']
b.shape
plt.ion()
plt.imshow(b[0].transpose(1,2,0))
b[0]
%hist -f viewimg.py
