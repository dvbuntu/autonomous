import math
import random
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches
from operator import itemgetter
from matplotlib.lines import Line2D

THR = 1500
STR = 1500

accel = 0;
speed = 0;

STR_ANGLE = 180


str_max = 1000
str_center = 1500
str_min = 2000

TIME = 0

def getAngle(str_pos = 1500, str_max_angle= 180):
  aa = (str_pos - 1000) * (str_max_angle / 1000)
  return aa

def getVelocity(accel, time):
  velocity = accel * time
  return velocity

def getAccel(v_init = 0.0, v_fin = 0.0 , t_init = 0.0, t_fin = 0.0):
  accel = (v_fin - v_init ) / (t_fin - t_init)
  return accel

def getVf(v_init, accel, t_t):
  Vf = v_init + accel * t_t
  return Vf


print(getAngle(1500, 180))

v_init = 20
v_final = 50
t_init = 10
t_final = 30
acl = getAccel(v_init, v_final, t_init, t_final)
v_f = getVf(v_init, acl, t_final - t_init)

print(acl)
print(v_f)

XYpos = (2,3)

def getXYPos(angle, velocity):
  xx = math.cos(angle) * velocity
  yy = math.sin(angle) * velocity
  return (xx, yy)


getXYPos(math.radians( 32.7), 16.6 )
getXYPos(math.radians( 90), 16.6 )


## simulate driving

str_max_angle = 100
verts  = [(0.0, 0.0)]
codes = [Path.MOVETO]
last_pos =  0

for tick in range(0,10):
  print (tick)
  heading = random.randrange(str_max_angle)
  print(heading)
  fwd_energy = random.randrange(10,500)
  print(fwd_energy)
  last_pos = fwd_energy + last_pos
  verts.append(getXYPos(math.radians(heading), last_pos))
  codes.append(Path.LINETO)

path = Path(verts, codes)

fig = plt.figure()
ax = fig.add_subplot(111)
patch = patches.PathPatch(path, facecolor='white',lw=3)
ax.add_patch(patch)
# x,y = zip(verts)
# line = Line2D(x,y)
#ax.add_line(line)
ax.set_xlim(min(verts,key=itemgetter(0))[0], max(verts,key=itemgetter(0))[0])
ax.set_ylim(min(verts,key=itemgetter(1))[1], max(verts,key=itemgetter(1))[1])
plt.show()


