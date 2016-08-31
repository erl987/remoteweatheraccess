from weathernetwork.common.airsensordataset import AirSensorDataset

class CombiSensorDataset(AirSensorDataset):
    """Single dataset of a combi sensor (temperature + humidity)."""

    def __init__(self, sensor_ID, temperature, humidity):
        """
        Constructor.
        :param sensor_ID:       ID of the sensor
        :type sensor_ID:        string
        :param temperature:     temperature value of that dataset [°C]
        :param humidity:        humidity value of that dataset [%]
        """
        super(CombiSensorDataset, self).__init__(temperature, humidity)
        self._sensor_ID = sensor_ID


    def get_sensor_ID(self):
        """
        Returns the sensor ID.
        :return:                sensor ID
        :rtype:                 string
        """
        return self._sensor_ID
