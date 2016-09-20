class CombiSensorArray(object):
    """
    Array of combi sensors measuring temperature + humidity.
    """
    
    def __init__(self):
        """
        Constructor.
        """
        self._sensors = dict()


    def add_sensor(self, sensor_ID, sensor_data):
        """
        Adss a sensor with its data.
        TODO
        :param sensor_data:     Sensor data (temperature + humidity)
        :type sensor_data:      Object of type AirSensorDataset
        """
        self._sensors[sensor_ID] = sensor_data


    def remove_sensor(self, sensor_ID):
        del self._sensors[sensor_ID]


    def get_sensor(self, sensor_ID):
        return self._sensors[sensor_ID]