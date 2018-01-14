Remote Weather Access
=====================

Features
--------

* Client/server solution for transferring weather data from multiple remote clients to a server via any network connection
* It currently supports weatherstations derived from the type TE923 (for example IROX PRO-X USB)
* Even a server based on a Raspberry Pi 2 is suitable for dozens of stations
* Clients can very small IoT-devices, for example Raspberry Pi 1
* Based on FTP-transfer of CSV-files (in a format specified for the software PCWetterstation)
* Operating system independent, installation packages are only provided for Debian Linux and compatible OS (Ubuntu, Raspbian, ...)


Client
------

The client software is currently legacy code, see :file:'./docs/README_client.txt' for some further documentation.


Quickstart
----------

* Build the installation package for Debian
* Install the server software and satisfy all dependencies
* Add a weather station to the weather database
* Add the combi sensors to the weather database
* Restart the server


Further information
-------------------

See the documentation in :file:'./docs/sphinx/source/server.rst'.
