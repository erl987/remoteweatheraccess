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
        :param latitude:            latitude [°]
        :type latitude:             float
        :param longitude:           longitude [°]
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
        :return:                    latitude [°], longitude [°], height [m above sea level]
        :rtype:                     float, float, float
        """
        return self._latitude, self._longitude, self._height
