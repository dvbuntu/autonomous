#!/usr/bin/python3

import numpy as np

w, h = 512, 512
data = np.zeros((h, w, 3), dtype=np.uint8)
data[256, 256] = [255, 0, 0]


from matplotlib import pyplot as plt
plt.imshow(data, interpolation='nearest')
plt.show()