from abc import ABCMeta, abstractmethod
from weathernetwork.server.exceptions import NotExistingError

class ISensor(metaclass=ABCMeta):
    """Interface class for all sensors."""

    def __init__(self, sensor_ID):
        self._sensor_ID = sensor_ID


    def get_sensor_ID(self):
        """
        Obtains the sensor ID.
        """
        return self._sensor_ID


    @abstractmethod
    def get_sensor_value(self, subsensor_ID):
        pass


    @abstractmethod
    def get_description(self, subsensor_ID):
        pass


    @abstractmethod
    def get_unit(self, subsensor_ID):
        pass


    @abstractmethod
    def get_subsensor_IDs(self):
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


    def get_sensor_value(self, subsensor_ID):
        if subsensor_ID == RainSensorData.PERIOD:
            value = self._amount
        elif subsensor_ID == RainSensorData.CUMULATED:
            value = self._cumulated_amount
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a rain sensor" % subsensor_ID)

        return value


    def get_description(self, subsensor_ID):
        if subsensor_ID == RainSensorData.PERIOD:
            description = "rain"
        elif subsensor_ID == RainSensorData.CUMULATED:
            description = "cumulated rain"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a rain sensor" % subsensor_ID)

        return description


    def get_unit(self, subsensor_ID):
        if subsensor_ID == RainSensorData.PERIOD:
            unit = "mm"
        elif subsensor_ID == RainSensorData.CUMULATED:
            unit = "mm"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a rain sensor" % subsensor_ID)

        return unit


    def get_subsensor_IDs(self):
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


    def get_sensor_value(self, subsensor_ID):
        if subsensor_ID == WindSensorData.AVERAGE:
            value = self._average
        elif subsensor_ID == WindSensorData.GUSTS:
            value = self._gusts
        elif subsensor_ID == WindSensorData.DIRECTION:
            value = self._direction
        elif subsensor_ID == WindSensorData.WIND_CHILL:
            value = self._wind_chill
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a wind sensor" % subsensor_ID)

        return value


    def get_description(self, subsensor_ID):
        if subsensor_ID == WindSensorData.AVERAGE:
            description = "average wind speed"
        elif subsensor_ID == WindSensorData.GUSTS:
            description = "max. wind gust"
        elif subsensor_ID == WindSensorData.DIRECTION:
            description = "wind direction"
        elif subsensor_ID == WindSensorData.WIND_CHILL:
            description = "wind chill temperature"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a wind sensor" % subsensor_ID)
            
        return description


    def get_unit(self, subsensor_ID):
        if subsensor_ID == WindSensorData.AVERAGE:
            unit = "km/h"
        elif subsensor_ID == WindSensorData.GUSTS:
            unit = "km/h"
        elif subsensor_ID == WindSensorData.DIRECTION:
            unit = "\N{DEGREE SIGN}"
        elif subsensor_ID == WindSensorData.WIND_CHILL:
            unit = "\N{DEGREE SIGN}C"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a wind sensor" % subsensor_ID)
            
        return unit


    def get_subsensor_IDs(self):
        return [WindSensorData.AVERAGE, WindSensorData.GUSTS, WindSensorData.DIRECTION, WindSensorData.WIND_CHILL]


class CombiSensorData(ISensor):
    """Data of a combi sensor (temperature / humidity)."""

    # name tags defining the subsensor types
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"

    def __init__(self, sensor_ID, temperature, humidity, description = []):
        super(self.__class__, self).__init__(sensor_ID)
        self._temperature = temperature
        self._humidity = humidity
        self._description = description


    def get_all_data(self):
        return self._temperature, self._humidity


    def get_sensor_value(self, subsensor_ID):
        if subsensor_ID == CombiSensorData.TEMPERATURE:
            value = self._temperature
        elif subsensor_ID == CombiSensorData.HUMIDITY:
            value = self._humidity
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a combi sensor" % subsensor_ID)

        return value


    def get_description(self, subsensor_ID):
        if subsensor_ID == CombiSensorData.TEMPERATURE:
            description = "temperature"
        elif subsensor_ID == CombiSensorData.HUMIDITY:
            description = "humidity"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a combi sensor" % subsensor_ID)
          
        if self._description:
            description += " (" + self._description + ")"
        else:
            description += " (" + super(self.__class__, self).get_sensor_ID() + ")"

        return description
 

    def get_combi_sensor_description(self):
        return self._description


    def get_unit(self, subsensor_ID):
        if subsensor_ID == CombiSensorData.TEMPERATURE:
            unit = "\N{DEGREE SIGN}C"
        elif subsensor_ID == CombiSensorData.HUMIDITY:
            unit = "%"
        else:
             raise NotExistingError("Invalid subsensor \"%s\" for a combi sensor" % subsensor_ID)
            
        return unit


    def get_subsensor_IDs(self):
        return [CombiSensorData.TEMPERATURE, CombiSensorData.HUMIDITY]


class BaseStationSensorData(ISensor):
    """Data of a base station."""

    # name tags defining the subsensor types
    BASE_STATION = "baseStation"
    PRESSURE = "pressure"
    UV = "UV"

    def __init__(self, pressure, UV):
        super(self.__class__, self).__init__(BaseStationSensorData.BASE_STATION)
        self._pressure = pressure
        self._UV = UV


    def get_all_data(self):
        return self._pressure, self._UV


    def get_sensor_value(self, subsensor_ID):
        if subsensor_ID == BaseStationSensorData.PRESSURE:
            value = self._pressure
        elif subsensor_ID == BaseStationSensorData.UV:
            value = self._UV
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a base station sensor" % subsensor_ID)

        return value


    def get_description(self, subsensor_ID):
        if subsensor_ID == BaseStationSensorData.PRESSURE:
            description = "pressure"
        elif subsensor_ID == BaseStationSensorData.UV:
            description = "UV"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a base station sensor" % subsensor_ID)
            
        return description


    def get_unit(self, subsensor_ID):
        if subsensor_ID == BaseStationSensorData.PRESSURE:
            unit = "hPa"
        elif subsensor_ID == BaseStationSensorData.UV:
            unit = "UV-X"
        else:
            raise NotExistingError("Invalid subsensor \"%s\" for a base station sensor" % subsensor_ID)
            
        return unit


    def get_subsensor_IDs(self):
        return [BaseStationSensorData.PRESSURE, BaseStationSensorData.UV]


class WeatherStationMetadata(object):
    """Metadata of a weather station."""

    def __init__(self, station_ID, device_info, location_info, latitude, longitude, height, rain_calib_factor):
        """
        Constructor.
        :param station_ID:          station ID
        :type station_ID:           string
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
        self._station_ID = station_ID
        self._device_info = device_info
        self._location_info = location_info
        self._latitude = latitude
        self._longitude = longitude
        self._height = height
        self._rain_calib_factor = rain_calib_factor


    def get_station_ID(self):
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