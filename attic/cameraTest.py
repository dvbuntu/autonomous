from PIL import Image, ImageDraw
import pygame.image
import sys
import pygame.camera
from pygame.locals import *

pygame.camera.init()

# initialize webcam
print('initialize webcam')
cams = pygame.camera.list_cameras()
print(cams)
cam = pygame.camera.Camera(cams[0],(512,1080),'RGB')
cam.start()

img = cam.get_image()
WIDTH = img.get_width()
HEIGHT = img.get_height()
screen = pygame.display.set_mode( ( WIDTH, HEIGHT ) )
pygame.display.set_caption("pyGame Camera View")
# screen.blit(img, (0,0))
#     pygame.display.flip()

while True :
     for e in pygame.event.get() :
         if e.type == pygame.QUIT :
             sys.exit()

     # draw frame
     screen.blit(img, (0,0))
     pygame.display.flip()
     # grab next frame    
     img = cam.get_image()


#cam.stop()
#cam.close()

