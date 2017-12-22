# service level running for data collection
ottoMicroLogger.py has a symlink in /usr/local/bin, which is called by ottoMicroLogger.service, 
located in /lib/systemd/system. To enable the service, run 
	sudo systemctl enable ottoMicroLogger.service 
once on the system. This will cause the service to be started when the system is started. 
To manually start the service, run 
	sudo systemctl start ottoMicroLogger.service
To manually stop:
	sudo systemctl stop ottoMicroLogger.service
To check status of ottoMicroLogger.py:
	sudo systemctl status ottoMicroLogger.service
To see output of ottoMicroLogger.py for debugging:
	sudo journalctl -u ottoMicroLogger.service



