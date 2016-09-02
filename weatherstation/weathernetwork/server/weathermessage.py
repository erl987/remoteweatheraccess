class WeatherMessage(object):
    """description of class"""

    def __init__(self, message_ID, station_ID, data):
        self._message_ID = message_ID
        self._station_ID = station_ID
        self._data = data


    def get_data(self):
        return self._data


    def get_station_ID(self):
        return self._station_ID


    def get_message_ID(self):
        return self._message_ID
