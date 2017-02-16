# RemoteWeatherAccess - Weather network connecting to remote stations
# Copyright(C) 2013-2016 Ralf Rettig (info@personalfme.de)
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

from setuptools import setup

# build the Debian package with: debuild -b -uc -us

setup(
    name='remote-weather-access',
    version='0.2.0',
    packages=['.', 'weathernetwork.common', 'weathernetwork.server'],
    package_dir={'': '.'},
    url='https://github.com/erl987/remoteweatheraccess',
    license='GNU General Public License 3 or newer',
    author='Ralf Rettig',
    author_email='info@personalfme.de',
    description='Weather network software (client + server) for collecting data from remote weather stations',
    install_requires=[
        'watchdog',
        'tblib',
        'nose',
        'scikit-image',
        'scipy',
        'matplotlib'
    ],
    data_files=[
        ('/lib/systemd/system', ['debian/remote-weather-access.service']),
        ('/etc/remote-weather-access', ['exampleConfig/config_ftp_weather_server.ini'])
    ]
)
