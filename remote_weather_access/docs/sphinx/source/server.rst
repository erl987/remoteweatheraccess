Remote Weather Access
=====================

Features
--------

* Client/server solution for transfering weather data from multiple remote clients to a server via any network connection
* Even a server based on a Raspberry Pi 2 is suitable for dozens of stations
* Clients can very small IoT-devices, for example Raspberry Pi 1
* Based on FTP-transfer of CSV-files (in a format specified for the software PCWetterstation)
* Operating system independent, installation packages are only provided for Debian Linux and compatible OS (Ubuntu, Raspbian, ...)


Client
------

The client software is currently legacy code, see :file:`README_client.txt` for some further documentation.


Quickstart
----------

* Build the installation package for Debian (see `Package building`_)
* Install the server software and satisfy all dependencies (see `Installation`_ and `Dependencies`_)
* Add a weather station to the weather database (see `Configuring the weather stations`_)
* Add the combi sensors to the weather database (see `Configuring the combi (temperature/humidity) sensors`_)
* Restart the server (see `Weather server`_)



Dependencies
------------

The weather server requires at least Python 3.4. It depends on the Python packages described in the following.

Packages that can be automatically installed by the Debian installer:

* tblib
* nose
* scikit-image
* scipy
* matplotlib


Package that has to be manually provided by installing via pip:

* watchdog

Install that package by:

.. code-block:: bash

	pip3 install watchdog



Package building
----------------

While the weather server in principle runs on all operating systems, only a package builder for Debian-based operating systems is provided (tested for Debian 8). A built package will be running on all platforms. Therefore it is not required to build the package on the target system.

Requirements
~~~~~~~~~~~~

The package stdeb for Python 3 is required:

.. code-block:: bash

	pip3 install stdeb


Steps to build a Debian-package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Unzip the source code in a suitable directory and change to that directory
* Build the Python source package, it will be located in the 
  sudirectory :file:`./dist`:

.. code-block:: bash

    python3 setup.py sdist

* Build the Debian binary package, it will be located in the 
  sudirectory :file:`./deb_dist`:

.. code-block:: bash

    py2dsc-deb dist/remote-weather-access-0.2.0.tar.gz



Installation
------------

The weather server is installed using the binary Debian-package:

.. code-block:: bash

    sudo dpkg -i ./deb_dist/python3-remote-weather-access_0.2.0-1_all.deb


Missing dependencies can finally be installed by:

.. code-block:: bash

	sudo apt-get -f install


After the installation, the weather server is configured as a daemon and running in the background. However, it is not yet functional because no weather station has been configured up to now. You need to add your weather station (see `Configuring the weather stations`_) and your combi sensors to the weather database (see `Configuring the combi (temperature/humidity) sensors`_).

Check that the server is running:

.. code-block:: bash

	sudo systemctl status weatherserver

This command should return :command:`active (running)` if everything is ok:

.. code-block:: bash
 
	● weatherserver.service - remote-weather-access server daemon
	   Loaded: loaded (/lib/systemd/system/weatherserver.service; enabled; vendor pr
	   Active: active (running) since Sa 2017-04-15 19:21:17 CEST; 2h 37min ago
	 Main PID: 1918 (weatherserver)
	   CGroup: /system.slice/weatherserver.service
		   ├─1918 /usr/bin/python3 /usr/bin/weatherserver /etc/remote-weather-ac
		   ├─1985 /usr/bin/python3 /usr/bin/weatherserver /etc/remote-weather-ac
		   ├─1986 /usr/bin/python3 /usr/bin/weatherserver /etc/remote-weather-ac
		   └─1987 /usr/bin/python3 /usr/bin/weatherserver /etc/remote-weather-ac

	Apr 15 19:21:17 developer-VirtualBox systemd[1]: Started remote-weather-access s
	lines 1-11/11 (END)


Uninstallation
--------------

The weather server is uninstalled as follows. If the configuration files should be kept, use:

.. code-block:: bash

	sudo apt-get remove python3-remote-weather-access

If the configuration files should be removed as well, use:

.. code-block:: bash

	sudo apt-get purge python3-remote-weather-access

However, even if using purge, the data files created by the server will not be deleted.


Configuration of the server
---------------------------

The server suite consists of several separate daemons and configuration programs. The relevant directories for the operation of the server are:

==============================	==========================================
directory			description
==============================	==========================================
/etc/remote-weather-access	configuration files
/var/lib/remote-weather-access	all data files and configuration templates
/var/log/remote-weather-access	server log files
==============================	==========================================


Weather server
~~~~~~~~~~~~~~

The weather server is parsing the data files received via FTP from the weather station clients and stores the data in the main weather database. It is running as daemon and started and stopped as follows:

.. code-block:: bash
	
	sudo systemctl start weatherserver

.. code-block:: bash

	sudo systemctl stop weatherserver


After a change of the configuration, a restart of the daemon is required:

.. code-block:: bash

	sudo systemctl restart weatherserver


The central configuration file for the weather server is the file :file:`/etc/remote-weather-access/weatherserver.ini`. It allows to adjust all settings. The default settings are suitable for most machines.

The weather data for all stations is stored in the database file defined in the configuration. By default its location is :file:`/var/lib/remote-weather-access/weather.db` and should not be edited manually.


The weather database needs to be configured to contain the required client weather stations as well as the combi (temperature/humidity) sensors that are normally connected to the weather stations. As they may be varying in their purpose (inside, outside, ...) and number, they need to be specified separately.


Configuring the weather stations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The weather stations in the database are configured using the command line tool :command:`manage-weather-stations`. A weather station is added by:

.. code-block:: bash

	sudo manage-weather-stations --add /var/lib/remote-weather-access/templates/new_station.json /var/lib/remote-weather-access/weather.db

Note that you should use root rights in order to obtain write access to the weather database that is normally owned by the weather daemon user. You need to adapt the JSON-configuration file to contain your station metadata. The command line tool :command:`manage-weather-stations` helps in all tasks related to managing the stations in the database. You can get detailed information using:

.. code-block:: bash

	manage-weather-stations --help



Configuring the combi (temperature/humidity) sensors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The combi sensors in the database are configured using the command line tool :command:`manage-weather-combi-sensors`. Combi sensors are variable sensors that may have varying purposes are therefore are not provided by default in the database. The sensor is identified by its name. Several stations can use sensors with an identical name. Combi sensors are added by:

.. code-block:: bash

	sudo manage-weather-combi-sensors --add /var/lib/remote-weather-access/templates/new_combi_sensors.json /var/lib/remote-weather-access/weather.db

Note also here that you should use root rights. Several combi sensors can be added at once in the JSON-configuration file. Also the command line tool :command:`manage-weather-combi-sensors` helps in all tasks related to managing the combi sensors. Detailed information is available using:

.. code-block:: bash

	manage-weather-combi-sensors --help



Weather data plotting
~~~~~~~~~~~~~~~~~~~~~

For each weather station in the database, a new data plot is automatically generated every 10 minutes. The details are configured in the file :file:`/etc/remote-weather-access/weatherplot.ini`. Most default settings should be appropriate, possibly the sensors to be plotted have to be adjusted.

The plots are stored in the directory :file:`/var/lib/remote-weather-access/plots` in one subdirectory for each station. Web front-ends can directly use these files for presenting the weather data to the user.


Weather data export
~~~~~~~~~~~~~~~~~~~

The weather data of each station is exported once per hour into CSV-files that are formatted as specified for the software PCWetterstation. The CSV-files are stored in subdirectories of the directory :file:`/var/lib/remote-weather-access/export`. The data in these directories can be for example provided via a FTP-server. The exporting is configured in the file :file:`/etc/remote-weather-access/weatherexport.ini`.


Interfaces to front-ends
------------------------

The server provides data for the usage by front-ends in the following directories:

================================================	==========================	================================
directory						file name			purpose
================================================	==========================	================================
/var/lib/remote-weather-access/plots/STATION-ID		weather_of_last_7_days.png	weather data plot
/var/lib/remote-weather-access/export/STATION_ID	EXPmm_YY.csv			complete data of the month yy/MM
================================================	==========================	================================

These files are updated automatically in certain periods.


License
-------

RemoteWeatherAccess - Weather network connecting to remote stations
Copyright(C) 2013-2017 Ralf Rettig (info@personalfme.de)

This program is free software: you can redistribute it and / or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.If not, see <http://www.gnu.org/licenses/>

