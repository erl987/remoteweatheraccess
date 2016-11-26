class WeatherMessage(object):
    """description of class"""

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
