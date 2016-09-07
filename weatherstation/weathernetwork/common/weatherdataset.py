import datetime

class WeatherDataset(object):
    """Weather data set at a moment in time."""

    def __init__(self, time, combi_sensor_vals, rain_gauge, pressure, UV, wind_direction, wind_speed, wind_gust, wind_temp):
        """
        Constructor.
        :param time:                timepoint of the dataset
        :type time:                 datetime
        :param combi_sensor_vals:   contains the combi sensor datasets
        :type combi_sensor_vals:    list containing several combi sensor objects (of type CombiSensorDataset)
        :param rain_gauge:          rain gauge value [mm]
        :type rain_gauge:           float
        :param pressure:            pressure [hPa]
        :type pressure:             float
        :param UV:                  UV-index [-]
        :type UV:                   float
        :param wind_direction:      wind direction [°]
        :type wind_direction:       float
        :param wind_speed:          average wind speed [km/h]
        :type wind_speed:           float
        :param wind_gust:           maximum wind gust [km/h]
        :type wind_gust:            float
        :param wind_temp:           wind sensor temperature [°C]
        :type wind_temp:            float
        :raise ValueError:          if a value has an invalid type
        """
        if type(time) is not datetime.datetime:
            raise ValueError('time must be a datetime.datetime, not a %s' % type(arg))
        self._time = time
        self._combi_sensor_vals = combi_sensor_vals
        self._rain_gauge = float(rain_gauge)
        self._pressure = float(pressure)
        self._UV = float(UV);
        self._wind_direction = float(wind_direction)
        self._wind_speed = float(wind_speed)
        self._wind_gust = float(wind_gust)
        self._wind_temp = float(wind_temp)

    def get_time(self):
        """
        Returns the timepoint of the dataset.
        :return:    Timepoint of the dataset
        :rtype:     Datetime
        """
        return self._time

    def get_combi_sensor_vals(self):
        """
        Returns the combi sensor values.
        :return:                combi sensor values (sensorID + temperature + humidity)
        :rtype:                 list of CombiSensorDataset objects
        """
        return self._combi_sensor_vals

    def get_rain_gauge(self):
        """
        Returns the raing gauge value.
        :return:                rain gauge value at the given timepoint [mm]
        :rtype:                 float
        """
        return self._rain_gauge

    def get_pressure(self):
        """
        Returns the pressure.
        :return:                pressure at the given timepoint [hPa]
        :rtype:                 float
        """
        return self._pressure

    def get_UV(self):
        """
        Returns the UV-index.
        :return:                UV-index at the given timepoint [-]
        :rtype:                 float
        """
        return self._UV

    def get_wind(self):
        """
        Returns the wind sensor data.
        :return:                wind direction [°], average wind speed [km/h], maximum wind gust [km/h], wind sensor temperature [°C]
        :rtype:                 float, float, float, float
        """
        return self._wind_direction, self._wind_speed, self._wind_gust, self._wind_temp
