class WeatherDataset(object):
    """Weather data at a moment in time"""

    def __init__(self, time, temp, humidity, rain_gauge, pressure, UV, wind_direction, wind_speed, wind_gust, wind_temp):
        self._time = time
        self._temp =  temp
        self._humidity = humidity
        self._rain_gauge = rain_gauge
        self._pressure = pressure
        self._UV = UV;
        self._wind_direction = wind_direction
        self._wind_speed = wind_speed
        self._wind_gust = wind_gust
        self._wind_temp = wind_temp

    def get_time(self):
        return self._time

    def get_temperature(self):
        return self._temp

    def get_humidity(self):
        return self._humidity

    def get_rain_gauge(self):
        return self._rain_gauge

    def get_pressure(self):
        return self._pressure

    def get_UV(self):
        return self._UV

    def get_wind(self):
        return self._wind_direction, self._wind_speed, self._wind_gust, self._wind_temp


