# remoteweatheraccess
Weather network software (client + server) for collecting data from remote weather stations.

This project contains a client and a server software and is written in Python. It currently supported weatherstations derived from the type TE923 (for example IROX PRO-X USB).

The programs are written in Python and require Python 3.3.

You will require the driver from that project:
http://te923.fukz.org/

Install it in the directory te923con.

Install a new Raspberry for a new station:

1. Clone the SD-card onto the new raspberry
2. Rename the computer in /etc/hostname and /etc/hosts
3. Set new WLAN-connection: set SSID and WLAN-key in /etc/network/interfaces
4. Replace the WiFi test IP in /usr/local/bin/testwifi.sh by the router address
5. Replace station file /opt/weatherstation/data/stationData.dat by the new one using python3.3 and the module "generate_stationfile.py" (owner + group: weatherstation)
6. Delete the last data storage file /opt/weatherstation/data/settings_###.dat (if existing)
7. Make sure that there are no data files EXP_##_##.CSV in the directory /opt/weatherstation/data/
8. Generate a new user on the FTP-server:
	htpasswd -p -b /etc/ftpd.passwd 'station name' $(openssl passwd -1 -noverify 'password')
	The warning can be ignored
	mkdir /srv/ftp/virtual/'station name'
	chown -R ftp:ftp /srv/ftp/virtual/'station_name'
9.	Adapt the file structure of the FTP-server:
	/srv/ftp/virtual/'station name'
		-> newData (ftp:ftp)
		-> newData/temp (weatherstation:weatherstation)
	chmod -w /srv/ftp/virtual/'station_name'	
	chmod +rwx /srv/ftp/virtual/'stationName'/newData
10. Generate internet page for the user
	mkdir  /srv/www/'station name'
	chown http-web:http-web /srv/www/'station name'
	cp /srv/www/ERL /srv/www/'station name'
	chown
	Adapt texts in /srv/www/'station name'/index.html
11.	Generate the data folder for the new station:
	mkdir /srv/weather/'station name'
	chown -R weatherstation:weatherstation /srv/weather/'station name'
12.	Add the station ftp-folder to incrod-control:
	incrontab -e -u weatherstation
	Add the line: /srv/ftp/virtual/'station name'/newData IN_CLOSE_WRITE python3 /opt/weatherstation/weatherserver.py $@/$#

-> The weather data can be obtained from http://station.com/'station name'
