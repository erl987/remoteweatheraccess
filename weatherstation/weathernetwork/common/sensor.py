class WindSensorData(object):
    """Data of a wind sensor."""

    def __init__(self, average, gusts, direction, wind_chill):
        self._average = average
        self._gusts = gusts
        self._direction = direction
        self._wind_chill = wind_chill


    def get_average_wind_speed(self):
        return self._average


    def get_gusts(self):
        return self._gusts


    def get_direction(self):
        return self._direction


    def get_wind_chill(self):
        return self._wind_chill


class CombiSensorData(object):
    """Data of a combi sensor (temperature / humidity)."""

    def __init__(self, sensor_ID, temperature, humidity):
        self._sensor_ID = sensor_ID
        self._temperature = temperature
        self._humidity = humidity


    def get_sensor_ID(self):
        return self._sensor_ID

    def get_temperature(self):
        return self._temperature


    def get_humidity(self):
        return self._humidity


class BaseStationSensorData(object):
    """Data of a base station."""

    def __init__(self, pressure, rain, UV):
        self._pressure = pressure
        self._rain = rain
        self._UV = UV


    def get_pressure(self):
        return self._pressure


    def get_rain(self):
        return self._rain


    def get_UV(self):
        return self._UV