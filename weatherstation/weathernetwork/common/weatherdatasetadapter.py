import datetime
from weathernetwork.common.weatherdataset import WeatherDataset
from weathernetwork.common.combisensorarray import CombiSensorArray
from switch import switch


class WeatherDatasetAdapter(object):
    """Adapter for access to weather datasets via strings."""

    # existing sensor IDs
    TEMP_INSIDE = "tempInside"
    HUMIDITY_INSIDE = "humidityInside"
    TEMP_OUTSIDE_1 = "tempOutside1"
    HUMIDITY_OUTSIDE_1 = "humidityOutside1"
    TEMP_OUTSIDE_2 = "tempOutside2"
    HUMIDITY_OUTSIDE_2 = "humidityOutside2"
    TEMP_OUTSIDE_3 = "tempOutside3"
    HUMIDITY_OUTSIDE_3 = "humidityOutside3"
    TEMP_OUTSIDE_4 = "tempOutside4"
    HUMIDITY_OUTSIDE_4 = "humidityOutside4"
    TEMP_OUTSIDE_5 = "tempOutside5"
    HUMIDITY_OUTSIDE_5 = "humidityOutside5"
    PRESSURE_SENSOR = "pressure"
    RAIN_SENSOR = "rain"
    UV_SENSOR = "UV"
    WIND_DIRECTION = "windDirection"
    WIND_SPEED = "windSpeed"
    WIND_GUST = "windGust"
    WIND_TEMP = "windTemp"

    # sensor descriptions
    DESCRIPTIONS = dict()
    DESCRIPTIONS[TEMP_INSIDE] = "inside temperature"
    DESCRIPTIONS[HUMIDITY_INSIDE] = "inside humidity"


    def __init__(self, parent):
        self._parent = parent


    def get(self, sensorStr):
        for case in switch(sensorStr):
            if case(WeatherDatasetAdapter.TEMP_INSIDE):
                return self._parent.get_combi_sensor(WeatherDatasetAdapter.TEMP_INSIDE).get_temperature()
                break
            if case(WeatherDatasetAdapter.HUMIDITY_INSIDE):
                return self._parent.get_combi_sensor_vals().get_humidity(CombiSensorArray.ID_IN)
                break
            if case(WeatherDatasetAdapter.TEMP_OUTSIDE_1):
                return self._parent.get_combi_sensor_vals().get_temperature(CombiSensorArray.ID_OUT_1)
                break
            if case(WeatherDatasetAdapter.HUMIDITY_OUTSIDE_1):
                return self._parent.get_combi_sensor_vals().get_humidity(CombiSensorArray.ID_OUT_1)
                break
            if case(WeatherDatasetAdapter.TEMP_OUTSIDE_2):
                return self._parent.get_combi_sensor_vals().get_temperature(CombiSensorArray.ID_OUT_2)
                break
            if case(WeatherDatasetAdapter.HUMIDITY_OUTSIDE_2):
                return self._parent.get_combi_sensor_vals().get_humidity(CombiSensorArray.ID_OUT_2)
                break
            if case(WeatherDatasetAdapter.TEMP_OUTSIDE_3):
                return self._parent.get_combi_sensor_vals().get_temperature(CombiSensorArray.ID_OUT_3)
                break
            if case(WeatherDatasetAdapter.HUMIDITY_OUTSIDE_3):
                return self._parent.get_combi_sensor_vals().get_humidity(CombiSensorArray.ID_OUT_3)
                break
            if case(WeatherDatasetAdapter.TEMP_OUTSIDE_4):
                return self._parent.get_combi_sensor_vals().get_temperature(CombiSensorArray.ID_OUT_4)
                break
            if case(WeatherDatasetAdapter.HUMIDITY_OUTSIDE_4):
                return self._parent.get_combi_sensor_vals().get_humidity(CombiSensorArray.ID_OUT_4)
                break
            if case(WeatherDatasetAdapter.TEMP_OUTSIDE_5):
                return self._parent.get_combi_sensor_vals().get_temperature(CombiSensorArray.ID_OUT_5)
                break
            if case(WeatherDatasetAdapter.HUMIDITY_OUTSIDE_5):
                return self._parent.get_combi_sensor_vals().get_humidity(CombiSensorArray.ID_OUT_5)
                break
            if case(WeatherDatasetAdapter.PRESSURE_SENSOR):
                return self._parent.get_pressure()
                break
            if case(WeatherDatasetAdapter.RAIN_SENSOR):
                return self._parent.get_rain_gauge()
                break
            if case(WeatherDatasetAdapter.UV_SENSOR):
                return self._parent.get_UV()
                break
            if case(WeatherDatasetAdapter.WIND_DIRECTION):
                return self._parent.get_wind()
                break
            if case(WeatherDatasetAdapter.WIND_SPEED):
                return self._parent.get_wind()
                break
            if case(WeatherDatasetAdapter.WIND_GUST):
                return self._parent.get_wind()
                break
            if case(WeatherDatasetAdapter.WIND_TEMP):
                return self._parent.get_wind()
                break
            if case():
                raise AssertionError("Invalid argument")
