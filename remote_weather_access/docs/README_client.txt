Install a new Raspberry for a new station:

1. Clone the SD-card onto the new raspberry
2. Rename the computer in /etc/hostname and /etc/hosts
3. Set new WLAN-connection: set SSID and WLAN-key in /etc/network/interfaces
4. Replace the WiFi test IP in /usr/local/bin/testwifi.sh by the router address
5. Replace station file /opt/weatherstation/data/stationData.dat by the new one using python3.3 and the module "generate_stationfile.py" (owner + group: weatherstation)
6. Delete the last data storage file /opt/weatherstation/data/settings_###.dat (if existing)
7. Make sure that there are no data files EXP_##_##.CSV in the directory /opt/weatherstation/data/
8. Generate a new user on the FTP-server:
	htpasswd -p -b /etc/vsftpd/ftpd.passwd 'station name' $(openssl passwd -1 -noverify 'password')
	The warning can be ignored
	mkdir /srv/ftp/virtual/'station name'
	chown -R vftpd:vsftpd /srv/ftp/virtual/'station_name'
9.	Adapt the file structure of the FTP-server:
	/srv/ftp/virtual/'station name'
		-> newData (vsftpd:vsftpd)
	chmod -w /srv/ftp/virtual/'station_name'	
	chmod +rwx /srv/ftp/virtual/'stationName'/newData
10. Generate internet page for the user
	mkdir  /srv/www/'station name'
	chown http-web:http-web /srv/www/'station name'
	cp /srv/www/ERL /srv/www/'station name'
	chown
	Adapt texts in /srv/www/'station name'/index.html

-> The weather data can be obtained from http://wetter.radixproductions.selfhost.me/'station name'
	