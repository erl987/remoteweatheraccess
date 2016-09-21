class WindSensorData(object):
    """Data of a wind sensor."""

    def __init__(self, average, gusts, direction, wind_chill):
        self._average = average
        self._gusts = gusts
        self._direction = direction
        self._wind_chill = wind_chill


    def get_average_wind_speed(self):
        return self._average


    def get_gusts(self):
        return self._gusts


    def get_direction(self):
        return self._direction


    def get_wind_chill(self):
        return self._wind_chill


class CombiSensorData(object):
    """Data of a combi sensor (temperature / humidity)."""

    def __init__(self, sensor_ID, temperature, humidity):
        self._sensor_ID = sensor_ID
        self._temperature = temperature
        self._humidity = humidity


    def get_sensor_ID(self):
        return self._sensor_ID

    def get_temperature(self):
        return self._temperature


    def get_humidity(self):
        return self._humidity


class BaseStationSensorData(object):
    """Data of a base station."""

    def __init__(self, pressure, rain, UV):
        self._pressure = pressure
        self._rain = rain
        self._UV = UV


    def get_pressure(self):
        return self._pressure


    def get_rain(self):
        return self._rain


    def get_UV(self):
        return self._UV


class WeatherStationMetadata(object):
    """Metadata of a weather station."""

    def __init__(self, station_ID, device_info, location_info, latitude, longitude, height):
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
        """
        self._station_ID = station_ID
        self._device_info = device_info
        self._location_info = location_info
        self._latitude = latitude
        self._longitude = longitude
        self._height = height

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