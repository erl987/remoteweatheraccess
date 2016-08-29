class AirDataset(object):
    """Single dataset of a measurement of air properties (temperature + humidity)"""

    def __init__(self, temperature, humidity):
        """
        Constructor
        """
        self._temperature = temperature
        self._humidity = humidity


    def get_temperature(self):
        return self._temperature


    def get_humidity(self):
        return self._humidity


