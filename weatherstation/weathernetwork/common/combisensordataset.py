from weathernetwork.common.airdataset import AirDataset

class CombiSensorDataset(AirDataset):
    """Single dataset of a combi sensor (temperature + humidity)"""

    def __init__(self, sensor_ID, temperature, humidity):
        """
        Constructor
        """
        super(CombiSensorDataset, self).__init__(temperature, humidity)
        self._sensor_ID = sensor_ID


    def get_sensor_ID(self):
        return self._sensor_ID
