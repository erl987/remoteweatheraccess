class WeatherStationMetadata(object):
    """metadata of a weather station"""

    def __init__(self, identifier, device_info, location_info, latitude, longitude, height):
        self._identifier = identifier
        self._device_info = device_info
        self._location_info = location_info
        self._latitude = latitude
        self._longitude = longitude
        self._height = height

    def get_identifier(self):
        return self._identifier

    def get_device_info(self):
        return self._device_info

    def get_location_info(self):
        return self._location_info

    def get_geo_info(self):
        return self._latitude, self._longitude, self._height
