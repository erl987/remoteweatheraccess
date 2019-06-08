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

from abc import ABCMeta, abstractmethod

from remote_weather_access.common.utilities import Comparable
from remote_weather_access.server.exceptions import NotExistingError


class Sensor(metaclass=ABCMeta):
    """Abstract base class for all sensors."""
    def __init__(self, sensor_id):
        """
        Constructor.

        :param sensor_id:           id of the sensor
        :type sensor_id:            str
        """
        self._sensor_id = sensor_id

    def get_sensor_id(self):
        """
        Obtains the sensor id.

        :return:                    id of the sensor
        :rtype:                     str
        """
        return self._sensor_id

    @abstractmethod
    def get_sensor_value(self, subsensor_id):
        """
        Obtains the sensor value.

        :param subsensor_id:        subsensor id
        :type subsensor_id:         str
        :return:                    the sensor value
        :rtype:                     float
        :raise NotExistingError:    if the subsensor id does not exist
        """
        pass

    @abstractmethod
    def get_description(self, subsensor_id):
        """
        Obtains the description of the sensor.

        :param subsensor_id:        subsensor id
        :type subsensor_id:         str
        :return:                    the description of the sensor
        :rtype:                     str
        :raise NotExistingError:    if the subsensor id does not exist
        """
        pass

    @abstractmethod
    def get_unit(self, subsensor_id):
        """
        Obtains the unit of the sensor value.

        :param subsensor_id:        subsensor id
        :type subsensor_id:         str
        :return:                    the unit of the sensor
        :rtype:                     str
        :raise NotExistingError:    if the subsensor id does not exist
        """
        pass

    @abstractmethod
    def get_subsensor_ids(self):
        """
        Obtains all subsensor ids of the sensor.

        :return:                    all subsensor ids of the sensor
        :rtype:                     list of str
        """
        pass


class RainSensorData(Sensor, Comparable):
    """Data of a rain sensor"""

    # name tags defining the subsensor types
    RAIN = "rain"
    PERIOD = "period"
    CUMULATED = "cumulated"

    def __init__(self, amount, begin_time, cumulated_amount=None, cumulation_begin_time=None):
        """
        Constructor.

        :param amount:                  Amount of rain within the present recording period (from begin to end time) [mm]
        :type amount:                   float
        :param begin_time:              Begin time of present recording, the end time needs to be stored by the caller
        :type begin_time:               datetime.datetime
        :param cumulated_amount:        Cumulated rain amount since the cumulation begin time [mm]
        :type cumulated_amount:         float
        :param cumulation_begin_time:   Cumulation begin time (i.e. the beginning of recording)
        :type cumulation_begin_time:    datetime.datetime
        """
        super(self.__class__, self).__init__(RainSensorData.RAIN)
        self._amount = amount
        self._begin_time = begin_time
        self._cumulated_amount = cumulated_amount
        self._cumulation_begin_time = cumulation_begin_time

    def get_all_data(self):
        """
        Obtains all rain data at once.

        :return:                    rain amount [mm], begin time, cumulated amount [mm], cumulation begin time
        :rtype:                     tuple(float, datetime.datetime, float, datetime.datetime)
        """
        return self._amount, self._begin_time, self._cumulated_amount, self._cumulation_begin_time

    def get_sensor_value(self, subsensor_id):
        """
        Obtains the sensor value.

        :param subsensor_id:        subsensor id
        :type subsensor_id:         str
        :return:                    the sensor value
        :rtype:                     float
        :raise NotExistingError:    if the subsensor id does not exist
        """
        if subsensor_id == RainSensorData.PERIOD:
            value = self._amount
        elif subsensor_id == RainSensorData.CUMULATED:
            value = self._cumulated_amount
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a rain sensor" % subsensor_id)

        return value

    def get_description(self, subsensor_id):
        """
        Obtains the description of the sensor.

        :param subsensor_id:        subsensor id
        :type subsensor_id:         str
        :return:                    the description of the sensor
        :rtype:                     str
        :raise NotExistingError:    if the subsensor id does not exist
        """
        if subsensor_id == RainSensorData.PERIOD:
            description = "Regen"
        elif subsensor_id == RainSensorData.CUMULATED:
            description = "Regen"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a rain sensor" % subsensor_id)

        return description

    def get_unit(self, subsensor_id):
        """
        Obtains the unit of the sensor value.

        :param subsensor_id:        subsensor id
        :type subsensor_id:         str
        :return:                    the unit of the sensor
        :rtype:                     str
        :raise NotExistingError:    if the subsensor id does not exist
        """
        if subsensor_id == RainSensorData.PERIOD:
            unit = "mm"
        elif subsensor_id == RainSensorData.CUMULATED:
            unit = "mm"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a rain sensor" % subsensor_id)

        return unit

    def get_subsensor_ids(self):
        """
        Obtains all subsensor ids of the sensor.

        :return:                    all subsensor ids of the sensor
        :rtype:                     list of str
        """
        return [RainSensorData.PERIOD, RainSensorData.CUMULATED]


class WindSensorData(Sensor, Comparable):
    """Data of a wind sensor."""

    # name tags defining the subsensor types
    WIND = "wind"
    AVERAGE = "average"
    GUSTS = "gusts"
    DIRECTION = "direction"
    WIND_CHILL = "windChill"

    def __init__(self, average, gusts, direction, wind_chill):
        """
        Constructor.

        :param average:             average wind speed in the recording period [km/h]
        :type average:              float
        :param gusts:               maximum gust in the recording period [km/h]
        :type gusts:                float
        :param direction:           wind direction in the recording period [degree]
        :type direction:            float
        :param wind_chill:          wind chill temperature in the recording period [degree Celsius]
        :type wind_chill:           float
        """
        super(self.__class__, self).__init__(WindSensorData.WIND)
        self._average = average
        self._gusts = gusts
        self._direction = direction
        self._wind_chill = wind_chill

    def get_all_data(self):
        """
        Obtains all wind sensor data at once.

        :return:                    average [km/h], maximum wind speed [km/h], wind direction [degree],
                                    wind chill temperature [°C]
        :rtype:                     tuple(float, float, float, float)
        """
        return self._average, self._gusts, self._direction, self._wind_chill

    def get_sensor_value(self, subsensor_id):
        """
        Obtains the sensor value.

        :param subsensor_id:        subsensor id
        :type subsensor_id:         str
        :return:                    the sensor value
        :rtype:                     float
        :raise NotExistingError:    if the subsensor id does not exist
        """
        if subsensor_id == WindSensorData.AVERAGE:
            value = self._average
        elif subsensor_id == WindSensorData.GUSTS:
            value = self._gusts
        elif subsensor_id == WindSensorData.DIRECTION:
            value = self._direction
        elif subsensor_id == WindSensorData.WIND_CHILL:
            value = self._wind_chill
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a wind sensor" % subsensor_id)

        return value

    def get_description(self, subsensor_id):
        """
        Obtains the description of the sensor.

        :param subsensor_id:        subsensor id
        :type subsensor_id:         str
        :return:                    the description of the sensor
        :rtype:                     str
        :raise NotExistingError:    if the subsensor id does not exist
        """
        if subsensor_id == WindSensorData.AVERAGE:
            description = "average wind speed"
        elif subsensor_id == WindSensorData.GUSTS:
            description = "max. wind gust"
        elif subsensor_id == WindSensorData.DIRECTION:
            description = "wind direction"
        elif subsensor_id == WindSensorData.WIND_CHILL:
            description = "wind chill temperature"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a wind sensor" % subsensor_id)

        return description

    def get_unit(self, subsensor_id):
        """
        Obtains the unit of the sensor value.

        :param subsensor_id:        subsensor id
        :type subsensor_id:         str
        :return:                    the unit of the sensor
        :rtype:                     str
        :raise NotExistingError:    if the subsensor id does not exist
        """
        if subsensor_id == WindSensorData.AVERAGE:
            unit = "km/h"
        elif subsensor_id == WindSensorData.GUSTS:
            unit = "km/h"
        elif subsensor_id == WindSensorData.DIRECTION:
            unit = "\N{DEGREE SIGN}"
        elif subsensor_id == WindSensorData.WIND_CHILL:
            unit = "\N{DEGREE SIGN}C"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a wind sensor" % subsensor_id)

        return unit

    def get_subsensor_ids(self):
        """
        Obtains all subsensor ids of the sensor.

        :return:                    all subsensor ids of the sensor
        :rtype:                     list of str
        """
        return [WindSensorData.AVERAGE, WindSensorData.GUSTS, WindSensorData.DIRECTION, WindSensorData.WIND_CHILL]


class CombiSensorData(Sensor, Comparable):
    """Data of a combi sensor (temperature / humidity)"""

    # name tags defining the subsensor types
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"

    def __init__(self, sensor_id, temperature, humidity, description=None):
        """
        Constructor.

        :param sensor_id:           combi sensor id
        :type sensor_id:            str
        :param temperature:         temperature [degree Celsius]
        :type temperature:          float
        :param humidity:            humidity [%]
        :type humidity:             float
        :param description:         sensor description
        :type description:          str
        """
        super(self.__class__, self).__init__(sensor_id)
        self._temperature = temperature
        self._humidity = humidity
        self._description = description

    def get_all_data(self):
        """
        Obtains all data of the sensor at once.

        :return:                    temperature [degree Celsius], humidity [%]
        :rtype:                     tuple(float, float)
        """
        return self._temperature, self._humidity

    def get_sensor_value(self, subsensor_id):
        """
        Obtains the sensor value.

        :param subsensor_id:        subsensor id
        :type subsensor_id:         str
        :return:                    the sensor value
        :rtype:                     float
        :raise NotExistingError:    if the subsensor id does not exist
        """
        if subsensor_id == CombiSensorData.TEMPERATURE:
            value = self._temperature
        elif subsensor_id == CombiSensorData.HUMIDITY:
            value = self._humidity
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a combi sensor" % subsensor_id)

        return value

    def get_description(self, subsensor_id):
        """
        Obtains the description of the sensor.

        :param subsensor_id:        subsensor id
        :type subsensor_id:         str
        :return:                    the description of the sensor
        :rtype:                     str
        :raise NotExistingError:    if the subsensor id does not exist
        """
        if subsensor_id == CombiSensorData.TEMPERATURE:
            description = "Temperatur"
        elif subsensor_id == CombiSensorData.HUMIDITY:
            description = "Feuchte"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a combi sensor" % subsensor_id)

        if self._description:
            description += " (" + self._description + ")"
        else:
            description += " (" + super(self.__class__, self).get_sensor_id() + ")"

        return description

    def get_combi_sensor_description(self):
        """
        Obtains the description of the combi sensor.

        :return:                    combi sensor description
        :rtype:                     str
        """
        return self._description

    def get_unit(self, subsensor_id):
        """
        Obtains the unit of the sensor value.

        :param subsensor_id:        subsensor id
        :type subsensor_id:         str
        :return:                    the unit of the sensor
        :rtype:                     str
        :raise NotExistingError:    if the subsensor id does not exist
        """
        if subsensor_id == CombiSensorData.TEMPERATURE:
            unit = "\N{DEGREE SIGN}C"
        elif subsensor_id == CombiSensorData.HUMIDITY:
            unit = "%"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a combi sensor" % subsensor_id)

        return unit

    def get_subsensor_ids(self):
        """
        Obtains all subsensor ids of the sensor.

        :return:                    all subsensor ids of the sensor
        :rtype:                     list of str
        """
        return [CombiSensorData.TEMPERATURE, CombiSensorData.HUMIDITY]


class BaseStationSensorData(Sensor, Comparable):
    """Data of a base station."""

    # name tags defining the subsensor types
    BASE_STATION = "baseStation"
    PRESSURE = "pressure"
    UV = "UV"

    def __init__(self, pressure, uv):
        """
        Constructor.

        :param pressure:            pressure [hPa]
        :type pressure:             float
        :param uv:                  UV-index
        :type uv:                   float
        """
        super(self.__class__, self).__init__(BaseStationSensorData.BASE_STATION)
        self._pressure = pressure
        self._uv = uv

    def get_all_data(self):
        """
        Obtains all data of the sensor at once.

        :return:                    pressure [hPa], UV-index
        :rtype:                     tuple(float, float)
        """
        return self._pressure, self._uv

    def get_sensor_value(self, subsensor_id):
        """
        Obtains the sensor value.

        :param subsensor_id:        subsensor id
        :type subsensor_id:         str
        :return:                    the sensor value
        :rtype:                     float
        :raise NotExistingError:    if the subsensor id does not exist
        """
        if subsensor_id == BaseStationSensorData.PRESSURE:
            value = self._pressure
        elif subsensor_id == BaseStationSensorData.UV:
            value = self._uv
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a base station sensor" % subsensor_id)

        return value

    def get_description(self, subsensor_id):
        """
        Obtains the description of the sensor.

        :param subsensor_id:        subsensor id
        :type subsensor_id:         str
        :return:                    the description of the sensor
        :rtype:                     str
        :raise NotExistingError:    if the subsensor id does not exist
        """
        if subsensor_id == BaseStationSensorData.PRESSURE:
            description = "Luftdruck"
        elif subsensor_id == BaseStationSensorData.UV:
            description = "UV"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a base station sensor" % subsensor_id)

        return description

    def get_unit(self, subsensor_id):
        """
        Obtains the unit of the sensor value.

        :param subsensor_id:        subsensor id
        :type subsensor_id:         str
        :return:                    the unit of the sensor
        :rtype:                     str
        :raise NotExistingError:    if the subsensor id does not exist
        """
        if subsensor_id == BaseStationSensorData.PRESSURE:
            unit = "hPa"
        elif subsensor_id == BaseStationSensorData.UV:
            unit = "UV-X"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a base station sensor" % subsensor_id)

        return unit

    def get_subsensor_ids(self):
        """
        Obtains all subsensor ids of the sensor.

        :return:                    all subsensor ids of the sensor
        :rtype:                     list of str
        """
        return [BaseStationSensorData.PRESSURE, BaseStationSensorData.UV]


class WeatherStationMetadata(Comparable):
    """Metadata of a weather station"""

    def __init__(self, station_id, device_info, location_info, latitude, longitude, height, rain_calib_factor):
        """
        Constructor.

        :param station_id:          station ID
        :type station_id:           string
        :param device_info:         device information (type of the device, possibly special configurations)
        :type device_info:          string
        :param location_info:       location information (City name, possible quarter or street)
        :type location_info:        string
        :param latitude:            latitude [degree]
        :type latitude:             float
        :param longitude:           longitude [degree]
        :type longitude:            float
        :param height:              height [m above sea level]
        :type height:               float
        :param rain_calib_factor:   calibration factor for the rain gauge sensor (1.0 if no correction is required)
        :type rain_calib_factor:    float
        """
        self._station_ID = station_id
        self._device_info = device_info
        self._location_info = location_info
        self._latitude = latitude
        self._longitude = longitude
        self._height = height
        self._rain_calib_factor = rain_calib_factor

    def get_station_id(self):
        """
        Returns the station ID.

        :return:                    station ID
        :rtype:                     str
        """
        return self._station_ID

    def get_device_info(self):
        """
        Returns the device information.

        :return:                    device information (type of the device, possibly special configurations)
        :rtype:                     str
        """
        return self._device_info

    def get_location_info(self):
        """
        Returns the location information.

        :return:                    location information (City name, possible quarter or street)
        :rtype:                     str
        """
        return self._location_info

    def get_geo_info(self):
        """
        Returns the geographical position information.

        :return:                    latitude [degree], longitude [degree], height [m above sea level]
        :rtype:                     tuple(float, float, float)
        """
        return self._latitude, self._longitude, self._height

    def get_rain_calib_factor(self):
        """
        Returns the rain gauge calibration factor.
        :return:                    rain gauge calibration factor (typically 1.0)
        :rtype:                     float
        """
        return self._rain_calib_factor


class WeatherStationDataset(Comparable):
    """Weather dataset at a moment in time"""

    def __init__(self, time):
        """
        Constructor.

        :param time:                timepoint
        :type time:                 datetime.datetime
        """
        self._time = time
        self._sensor_data = dict()

    def get_time(self):
        """
        Obtains the timepoint of the weather data.

        :return:                    timepoint
        :rtype:                     datetime.datetime
        """
        return self._time

    def contains(self, sensor_id):
        """
        Determines if the dataset contains data of the requested sensor.

        :param sensor_id:           required sensor id
        :type sensor_id:            str
        :return:                    if the dataset contains the requested sensor
        :rtype:                     bool
        """
        return sensor_id in self._sensor_data

    def get_sensor_value(self, sensor_id_tuple):
        """
        Obtains the signal data value of a specified sensor.

        :param sensor_id_tuple:     sensor id (consisting of {sensor id, subsensor id})
        :type sensor_id_tuple:      tuple(str,str)
        :return:                    value of the specified (sub-) sensor
        :rtype:                     float
        """
        sensor_id, subsensor_id = sensor_id_tuple

        try:
            value = self._sensor_data[sensor_id].get_sensor_value(subsensor_id)
        except:
            raise NotExistingError("No data for the sensor '{}'".format(sensor_id))

        return value

    def get_sensor_object(self, sensor_id):
        """
        Obtains the sensor data object of the requested sensor.

        :param sensor_id:           sensor id of the requested sensor
        :type sensor_id:            str
        :return:                    object of the sensor data
        """
        return self._sensor_data[sensor_id]

    def add_sensor(self, data):
        """
        Adds sensor data to the dataset.

        :param data:                object of the sensor data to be added
        :type data:                 Sensor
        """
        self._sensor_data[data.get_sensor_id()] = data

    def remove_sensor(self, sensor_id):
        """
        Removes sensor data from the dataset.

        :param sensor_id:           id of the sensor to be removed
        :type sensor_id:            str
        """
        del self._sensor_data[sensor_id]

    def get_sensor_description(self, sensor_id_tuple):
        """
        Obtains the unit of a certain sensor.

        :param sensor_id_tuple:     sensor id (consisting of {sensor id, subsensor id})
        :type sensor_id_tuple:      tuple(str,str)
        :return:                    sensor description
        :rtype:                     str
        """
        sensor_id, subsensor_id = sensor_id_tuple

        return self._sensor_data[sensor_id].get_description(subsensor_id)

    def get_sensor_unit(self, sensor_id_tuple):
        """
        Obtains the unit of a certain sensor.

        :param sensor_id_tuple:     sensor id (consisting of {sensor id, subsensor id})
        :type sensor_id_tuple:      tuple(str,str)
        :return:                    unit of the sensor
        :rtype:                     str
        """
        sensor_id, subsensor_id = sensor_id_tuple

        return self._sensor_data[sensor_id].get_unit(subsensor_id)

    def get_all_sensor_ids(self):
        """
        Obtains the ids of all sensors in the dataset.

        :return:                    the ids of all sensors present in the dataset (format: {sensor id, subsensor id})
        :rtype:                     dict(str, str)
        """
        sensor_ids = dict()
        for key, curr_sensor in self._sensor_data.items():
            sensor_ids[curr_sensor.get_sensor_id()] = curr_sensor.get_subsensor_ids()

        return sensor_ids


class WeatherMessage(Comparable):
    """Class representing a weather data message transmitted via network"""

    def __init__(self, message_id, station_id, data):
        """
        Constructor.

        :param message_id:          id of the message
        :type message_id:           str
        :param station_id:          id of the weather station
        :type station_id:           str
        :param data:                weather datasets
        :type data:                 list of WeatherStationDataset
        """
        self._message_id = message_id
        self._station_id = station_id
        self._data = data

    def get_data(self):
        """
        Obtains the weather data.

        :return:                    weather datasets
        :rtype:                     list of WeatherStationDataset
        """
        return self._data

    def get_station_id(self):
        """
        Obtains the id of the weather station.

        :return:                    weather station id
        :rtype:                     str
        """
        return self._station_id

    def get_message_id(self):
        """
        Obtains the id of the message.

        :return:                    message id
        :rtype:                     str
        """
        return self._message_id