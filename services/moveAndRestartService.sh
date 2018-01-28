#!/bin/bash

mv /home/pi/ottoMicroLogger.py ~/autonomous/services/
sudo systemctl stop ottoMicroLogger.service
sudo systemctl start ottoMicroLogger.service
sudo systemctl status ottoMicroLogger.service
