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


    def contains(self, sensor_id):
        return sensor_id in self._sensor_data


    def get_sensor_value(self, sensor_id_tuple):
        """
        Obtains the signal data value of a specified sensor.
        """
        sensor_id, subsensor_id = sensor_id_tuple

        return self._sensor_data[sensor_id].get_sensor_value(subsensor_id)


    def get_sensor_object(self, sensor_id):
        return self._sensor_data[sensor_id]


    def add_sensor(self, data):
        self._sensor_data[data.get_sensor_id()] = data


    def remove_sensor(self, sensor_id):
        del self._sensor_data[sensor_id]


    def get_sensor_description(self, sensor_id_tuple):
        """
        Obtains the unit of a certain sensor ID.
        """
        sensor_id, subsensor_id = sensor_id_tuple

        return self._sensor_data[sensor_id].get_description(subsensor_id)


    def get_sensor_unit(self, sensor_id_tuple):
        """
        Obtains the unit of a certain sensor ID.
        """
        sensor_id, subsensor_id = sensor_id_tuple

        return self._sensor_data[sensor_id].get_unit(subsensor_id)


    def get_all_sensor_ids(self):
        sensor_ids = dict()
        for key, curr_sensor in self._sensor_data.items():
            sensor_ids[curr_sensor.get_sensor_id()] = curr_sensor.get_subsensor_ids()

        return sensor_ids