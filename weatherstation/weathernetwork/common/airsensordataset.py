class AirSensorDataset(object):
    """Single dataset of a measurement of air properties (temperature + humidity)."""

    def __init__(self, temperature, humidity):
        """
        Constructor.
        :param temperature:         temperature value of the sensor [°C]
        :param humidity:            humidity value of the sensor [%]
        :raise ValueError:          if a value has an invalid type
        """
        self._temperature = float(temperature)
        self._humidity = float(humidity)


    def get_temperature(self):
        """
        Returns the temperature.
        :return:                    temperature value of the sensor [°C]
        """
        return self._temperature


    def get_humidity(self):
        """
        Returns the humidity.
        :return:                    humidity value of the sensor [%]
        """
        return self._humidity


