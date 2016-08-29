class WeatherDataset(object):
    """Weather data at a moment in time"""

    def __init__(self, time, combi_sensor_vals, rain_gauge, pressure, UV, wind_direction, wind_speed, wind_gust, wind_temp):
        """
        Constructor
        :param combi_sensor_vals:   contains the combi sensor datasets
        :type combi_sensor_vals:    list containing several combi sensor objects (of type CombiSensorDataset)
        """
        self._time = time
        self._combi_sensor_vals = combi_sensor_vals
        self._rain_gauge = rain_gauge
        self._pressure = pressure
        self._UV = UV;
        self._wind_direction = wind_direction
        self._wind_speed = wind_speed
        self._wind_gust = wind_gust
        self._wind_temp = wind_temp

    def get_time(self):
        return self._time

    def get_combi_sensor_vals(self):
        return self._combi_sensor_vals

    def get_rain_gauge(self):
        return self._rain_gauge

    def get_pressure(self):
        return self._pressure

    def get_UV(self):
        return self._UV

    def get_wind(self):
        return self._wind_direction, self._wind_speed, self._wind_gust, self._wind_temp
