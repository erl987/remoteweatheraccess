# RemoteWeatherAccess - Weather network connecting to remote stations
# Copyright(C) 2013-2017 Ralf Rettig (info@personalfme.de)
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.If not, see <http://www.gnu.org/licenses/>
import os

from setuptools import setup, find_packages

# build the Python source package (distribution-independent): python3 setup.py sdist
# build the Debian binary package (actually also distribution-independent):
# py2dsc-deb dist/remote-weather-access-0.2.0.tar.gz (requires the stdeb package for Python3)
# the created package is located in the subdirectory 'deb_dist'


def read(fname):
    """Text file reader."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='remote-weather-access',
    version='0.2.0',
    packages=find_packages(exclude=('tests', 'remote_weather_access.client')),
    package_dir={'': '.'},
    url='https://github.com/erl987/remoteweatheraccess',
    license='GNU General Public License 3 or newer',
    author='Ralf Rettig',
    author_email='info@personalfme.de',
    description='Weather network software for collecting data from remote stations',
    long_description=read('README.rst'),
    platforms='any',
    # 'watchdog' is an additional dependency, but is not provided as a Debian package (python3-watchdog)
    # on Raspbian, it therefore needs to be installed separately via pip (pip3 install watchdog)
    install_requires=[
        'tblib',
        'nose',
        'scikit-image',
        'scipy',
        'matplotlib'
    ],
    data_files=[
        ('/lib/systemd/system', ['debian/weatherserver.service']),
        ('/etc/remote-weather-access', ['config/weatherserver.ini', 'config/weatherplot.ini',
                                        'config/weatherexport.ini']),
        ('/etc/cron.d', ['debian/remote-weather-access-cron']),
        ('/var/lib/remote-weather-access/templates', ['config/new_station.json', 'config/new_combi_sensors.json'])
    ],
    entry_points={
        'console_scripts': [
            'weatherserver=remote_weather_access.ftp_weather_server:main',
            'manage-weather-combi-sensors=remote_weather_access.manage_db_combi_sensors:main',
            'manage-weather-stations=remote_weather_access.manage_db_stations:main',
            'weatherplot=remote_weather_access.plot_weather_graph:main',
            'export-weatherdata=remote_weather_access.export_weather_data:main'
        ],
    }
)
