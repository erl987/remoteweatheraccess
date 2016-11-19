class WeatherStationDataset(object):
    """Weather data set at a moment in time."""

    def __init__(self, time):
        """
        Constructor.
        """
        self._time = time
        self._sensor_data = dict()


    def get_time(self):
        return self._time


    def contains(self, sensor_ID):
        return sensor_ID in self._sensor_data


    def get_sensor_value(self, sensor_ID_tuple):
        """
        Obtains the signal data value of a specified sensor.
        """
        sensor_ID, subsensor_ID = sensor_ID_tuple

        return self._sensor_data[sensor_ID].get_sensor_value(subsensor_ID)


    def get_sensor_object(self, sensor_ID):
        return self._sensor_data[sensor_ID]


    def add_sensor(self, data):
        self._sensor_data[data.get_sensor_ID()] = data


    def remove_sensor(self, sensor_ID):
        del self._sensor_data[sensor_ID]


    def get_sensor_description(self, sensor_ID_tuple):
        """
        Obtains the unit of a certain sensor ID.
        """
        sensor_ID, subsensor_ID = sensor_ID_tuple

        return self._sensor_data[sensor_ID].get_description(subsensor_ID)


    def get_sensor_unit(self, sensor_ID_tuple):
        """
        Obtains the unit of a certain sensor ID.
        """
        sensor_ID, subsensor_ID = sensor_ID_tuple

        return self._sensor_data[sensor_ID].get_unit(subsensor_ID)


    def get_all_sensor_IDs(self):
        sensor_IDs = dict()
        for key, curr_sensor in self._sensor_data.items():
            sensor_IDs[curr_sensor.get_sensor_ID()] = curr_sensor.get_subsensor_IDs()

        return sensor_IDs