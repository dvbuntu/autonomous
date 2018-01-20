#!/usr/bin/python3

import sys, os
import subprocess
from subprocess import call
from subprocess import Popen, PIPE

# try to unmount the USB drive
#       if it is unmounted already, suppress the error message
#               and send the message to log.txt
#       otherwise remount it

call ( "/usr/bin/pumount /dev/sda1 2> ~/log.txt", shell=True )
call ( "/usr/bin/pmount /dev/sda1", shell=True )
call ( "ls /media/sda1", shell=True )
call ( "cp ~/test.txt /media/sda1", shell=True )