from abc import ABCMeta, abstractmethod
from weathernetwork.server.exceptions import NotExistingError


class ISensor(metaclass=ABCMeta):
    """Interface class for all sensors."""

    def __init__(self, sensor_id):
        self._sensor_id = sensor_id

    def get_sensor_id(self):
        """
        Obtains the sensor ID.
        """
        return self._sensor_id

    @abstractmethod
    def get_sensor_value(self, subsensor_id):
        pass

    @abstractmethod
    def get_description(self, subsensor_id):
        pass

    @abstractmethod
    def get_unit(self, subsensor_id):
        pass

    @abstractmethod
    def get_subsensor_ids(self):
        pass


class RainSensorData(ISensor):
    """Data of a rain sensor."""

    # name tags defining the subsensor types
    RAIN = "rain"
    PERIOD = "period"
    CUMULATED = "cumulated"

    def __init__(self, amount, begin_time, cumulated_amount=None, cumulation_begin_time=None):
        super(self.__class__, self).__init__(RainSensorData.RAIN)
        self._amount = amount
        self._begin_time = begin_time
        self._cumulated_amount = cumulated_amount
        self._cumulation_begin_time = cumulation_begin_time

    def get_all_data(self):
        return self._amount, self._begin_time, self._cumulated_amount, self._cumulation_begin_time

    def get_sensor_value(self, subsensor_id):
        if subsensor_id == RainSensorData.PERIOD:
            value = self._amount
        elif subsensor_id == RainSensorData.CUMULATED:
            value = self._cumulated_amount
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a rain sensor" % subsensor_id)

        return value

    def get_description(self, subsensor_id):
        if subsensor_id == RainSensorData.PERIOD:
            description = "rain"
        elif subsensor_id == RainSensorData.CUMULATED:
            description = "cumulated rain"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a rain sensor" % subsensor_id)

        return description

    def get_unit(self, subsensor_id):
        if subsensor_id == RainSensorData.PERIOD:
            unit = "mm"
        elif subsensor_id == RainSensorData.CUMULATED:
            unit = "mm"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a rain sensor" % subsensor_id)

        return unit

    def get_subsensor_ids(self):
        return [RainSensorData.PERIOD, RainSensorData.CUMULATED]


class WindSensorData(ISensor):
    """Data of a wind sensor."""

    # name tags defining the subsensor types
    WIND = "wind"
    AVERAGE = "average"
    GUSTS = "gusts"
    DIRECTION = "direction"
    WIND_CHILL = "windChill"

    def __init__(self, average, gusts, direction, wind_chill):
        super(self.__class__, self).__init__(WindSensorData.WIND)
        self._average = average
        self._gusts = gusts
        self._direction = direction
        self._wind_chill = wind_chill

    def get_all_data(self):
        return self._average, self._gusts, self._direction, self._wind_chill

    def get_sensor_value(self, subsensor_id):
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
        return [WindSensorData.AVERAGE, WindSensorData.GUSTS, WindSensorData.DIRECTION, WindSensorData.WIND_CHILL]


class CombiSensorData(ISensor):
    """Data of a combi sensor (temperature / humidity)."""

    # name tags defining the subsensor types
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"

    def __init__(self, sensor_id, temperature, humidity, description=None):
        super(self.__class__, self).__init__(sensor_id)
        self._temperature = temperature
        self._humidity = humidity
        self._description = description

    def get_all_data(self):
        return self._temperature, self._humidity

    def get_sensor_value(self, subsensor_id):
        if subsensor_id == CombiSensorData.TEMPERATURE:
            value = self._temperature
        elif subsensor_id == CombiSensorData.HUMIDITY:
            value = self._humidity
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a combi sensor" % subsensor_id)

        return value

    def get_description(self, subsensor_id):
        if subsensor_id == CombiSensorData.TEMPERATURE:
            description = "temperature"
        elif subsensor_id == CombiSensorData.HUMIDITY:
            description = "humidity"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a combi sensor" % subsensor_id)

        if self._description:
            description += " (" + self._description + ")"
        else:
            description += " (" + super(self.__class__, self).get_sensor_id() + ")"

        return description

    def get_combi_sensor_description(self):
        return self._description

    def get_unit(self, subsensor_id):
        if subsensor_id == CombiSensorData.TEMPERATURE:
            unit = "\N{DEGREE SIGN}C"
        elif subsensor_id == CombiSensorData.HUMIDITY:
            unit = "%"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a combi sensor" % subsensor_id)

        return unit

    def get_subsensor_ids(self):
        return [CombiSensorData.TEMPERATURE, CombiSensorData.HUMIDITY]


class BaseStationSensorData(ISensor):
    """Data of a base station."""

    # name tags defining the subsensor types
    BASE_STATION = "baseStation"
    PRESSURE = "pressure"
    UV = "UV"

    def __init__(self, pressure, uv):
        super(self.__class__, self).__init__(BaseStationSensorData.BASE_STATION)
        self._pressure = pressure
        self._uv = uv

    def get_all_data(self):
        return self._pressure, self._uv

    def get_sensor_value(self, subsensor_id):
        if subsensor_id == BaseStationSensorData.PRESSURE:
            value = self._pressure
        elif subsensor_id == BaseStationSensorData.UV:
            value = self._uv
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a base station sensor" % subsensor_id)

        return value

    def get_description(self, subsensor_id):
        if subsensor_id == BaseStationSensorData.PRESSURE:
            description = "pressure"
        elif subsensor_id == BaseStationSensorData.UV:
            description = "UV"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a base station sensor" % subsensor_id)

        return description

    def get_unit(self, subsensor_id):
        if subsensor_id == BaseStationSensorData.PRESSURE:
            unit = "hPa"
        elif subsensor_id == BaseStationSensorData.UV:
            unit = "UV-X"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a base station sensor" % subsensor_id)

        return unit

    def get_subsensor_ids(self):
        return [BaseStationSensorData.PRESSURE, BaseStationSensorData.UV]


class WeatherStationMetadata(object):
    """Metadata of a weather station."""

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
        :return:                    rain gauge calibration factor (typically 1.0)
        :rtype:                     float

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
        :return:        Station ID
        :rtype:         String
        """
        return self._station_ID

    def get_device_info(self):
        """
        Returns the device information.
        :return:                    device information (type of the device, possibly special configurations)
        :rtype:                     string
        """
        return self._device_info

    def get_location_info(self):
        """
        Returns the location information.
        :return:                    location information (City name, possible quarter or street)
        :rtype:                     string
        """
        return self._location_info

    def get_geo_info(self):
        """
        Returns the geographical position information.
        :return:                    latitude [degree], longitude [degree], height [m above sea level]
        :rtype:                     float, float, float
        """
        return self._latitude, self._longitude, self._height

    def get_rain_calib_factor(self):
        """
        Returns the rain gauge calibration factor.
        :return:                    rain gauge calibration factor (typically 1.0)
        :rtype:                     float
        """
        return self._rain_calib_factor
