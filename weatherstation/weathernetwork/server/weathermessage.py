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


class WeatherMessage(object):
    """Class representing a weather data message transmitted via network"""

    def __init__(self, message_id, station_id, data):
        self._message_id = message_id
        self._station_id = station_id
        self._data = data

    def get_data(self):
        return self._data

    def get_station_id(self):
        return self._station_id

    def get_message_id(self):
        return self._message_id
