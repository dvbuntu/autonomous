import numpy as np

dd_files = ['deepdrive.tfweights','deepdrive.tfweights2']

ddw = np.load(dd_files[0],encoding='latin1')
ddw2 = np.load(dd_files[1],encoding='bytes')

# extract into actual arrays, yeesh
keys = sorted(ddw.item().keys())
names = []
W = []
b = []
D = ddw.item()
for k in keys:
    v = D[k]
    names.append(k)
    W.append(v['weights'])
    b.append(v['biases'])

#keys2 = ddw2.item().keys()
#names2 = []
#W2 = []
#b2 = []
#for k,v in ddw2.item().items():
#    names2.append(k)
#    W2.append(v[b'weights'])
#    b2.append(v[b'biases'])
#
## They're identical
#for bb1,bb2 in zip(b,b2):
#    print(False in (bb1==bb2))
#           
#for bb1,bb2 in zip(W,W2):                                        
#    print(False in (bb1==bb2))

