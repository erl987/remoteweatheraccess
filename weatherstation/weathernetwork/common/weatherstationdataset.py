import datetime
from weathernetwork.common.switch import switch
from weathernetwork.server.exceptions import NotExistingError
from weathernetwork.common.sensor import WindSensorData, BaseStationSensorData, CombiSensorData

class WeatherStationDataset(object):
    """Weather data set at a moment in time."""

    # constants defining the data
    WIND = "wind"
    AVERAGE = "average"
    GUSTS = "gusts"
    DIRECTION = "direction"
    WIND_CHILL = "windChill"

    BASE_STATION = "baseStation"
    PRESSURE = "pressure"
    RAIN = "rain"
    UV = "UV"

    COMBI_SENSOR = "combiSensor"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"

    # definition of the sensor descriptions
    _sensor_descriptions = dict()
    _sensor_descriptions[PRESSURE] = "pressure"
    _sensor_descriptions[RAIN] = "rain"
    _sensor_descriptions[UV] = "UV"

    _wind_descriptions = dict()
    _wind_descriptions[AVERAGE] = "average wind speed"
    _wind_descriptions[GUSTS] = "max. wind gust"
    _wind_descriptions[DIRECTION] = "wind direction"
    _wind_descriptions[WIND_CHILL] = "wind chill temperature"
    _sensor_descriptions[WIND] = _wind_descriptions

    _combi_sensor_descriptions = dict()
    _combi_sensor_descriptions[TEMPERATURE] = "temperature"
    _combi_sensor_descriptions[HUMIDITY] = "humidity"
    _sensor_descriptions[COMBI_SENSOR] = _combi_sensor_descriptions

    def __init__(self, time):
        """
        Constructor.
        """
        self._time = time
        self._sensor_data = dict()


    @staticmethod
    def get_sensor_descriptions():
        return WeatherStationDataset._sensor_descriptions


    def get_time(self):
        return self._time


    @staticmethod
    def get_wind_sensor_data(dataset):
        time = dataset.get_time()
        wind_direction = dataset.get_sensor_value([WeatherStationDataset.WIND, WeatherStationDataset.DIRECTION])
        wind_average = dataset.get_sensor_value([WeatherStationDataset.WIND, WeatherStationDataset.AVERAGE])
        wind_gust = dataset.get_sensor_value([WeatherStationDataset.WIND, WeatherStationDataset.GUSTS])
        wind_chill_temp = dataset.get_sensor_value([WeatherStationDataset.WIND, WeatherStationDataset.WIND_CHILL])

        return time, wind_direction, wind_average, wind_gust, wind_chill_temp


    @staticmethod
    def get_base_station_sensor_data(dataset):
        time = dataset.get_time()
        pressure = dataset.get_sensor_value(WeatherStationDataset.PRESSURE)
        rain = dataset.get_sensor_value(WeatherStationDataset.RAIN)
        UV = dataset.get_sensor_value(WeatherStationDataset.UV)

        return time, pressure, rain, UV


    @staticmethod
    def get_combi_sensor_data(sensor_ID, dataset):
        time = dataset.get_time()
        if dataset.contains(sensor_ID):
            temperature = dataset.get_sensor_value([sensor_ID, WeatherStationDataset.TEMPERATURE])
            humidity = dataset.get_sensor_value([sensor_ID, WeatherStationDataset.HUMIDITY])
        else:
            temperature = None
            humidity = None

        return time, temperature, humidity


    def _get_wind_data(self, subsensor_ID):
        for case in switch(subsensor_ID):
            if case(WeatherStationDataset.AVERAGE):
                value = self._sensor_data[WeatherStationDataset.WIND].get_average_wind_speed()
                break
            if case(WeatherStationDataset.GUSTS):
                value = self._sensor_data[WeatherStationDataset.WIND].get_gusts()
                break
            if case(WeatherStationDataset.DIRECTION):
                value = self._sensor_data[WeatherStationDataset.WIND].get_direction()
                break
            if case(WeatherStationDataset.WIND_CHILL):
                value = self._sensor_data[WeatherStationDataset.WIND].get_wind_chill()
                break
            if case():
                raise NotExistingError("Invalid subsensor for a wind sensor")

        return value


    def _get_base_station_data(self, sensor_ID):
        for case in switch(sensor_ID):
            if case(WeatherStationDataset.PRESSURE):
                value = self._sensor_data[WeatherStationDataset.BASE_STATION].get_pressure()
                break
            if case(WeatherStationDataset.RAIN):
                value = self._sensor_data[WeatherStationDataset.BASE_STATION].get_rain()
                break
            if case(WeatherStationDataset.UV):
                value = self._sensor_data[WeatherStationDataset.BASE_STATION].get_UV()
                break
            if case():
                raise NotExistingError("Invalid subsensor for a base station")

        return value


    def _get_combi_sensor_data(self, sensor_ID, subsensor_ID):
        for case in switch(subsensor_ID):
            if case(WeatherStationDataset.TEMPERATURE):
                value = self._sensor_data[sensor_ID].get_temperature()
                break
            if case(WeatherStationDataset.HUMIDITY):
                value = self._sensor_data[sensor_ID].get_humidity()
                break
            if case():
                raise NotExistingError("Invalid subsensor for a combi sensor")

        return value


    def contains(self, sensor_ID):
        return sensor_ID in self._sensor_data


    def get_sensor_value(self, sensor_ID_list):
        """
        Obtains the signal data value of a specified (sub-) sensor.
        """
        if not isinstance(sensor_ID_list, list):
            sensor_ID_list = [sensor_ID_list]
        sensor_ID = sensor_ID_list[0]
        if len(sensor_ID_list) > 1:
            subsensor_ID = sensor_ID_list[1]
        else:
            subsensor_ID = None

        for case in switch(sensor_ID):
            if case(WeatherStationDataset.WIND):
                value = self._get_wind_data(subsensor_ID)
                break
            if case(WeatherStationDataset.PRESSURE):
                value = self._get_base_station_data(sensor_ID)
                break
            if case(WeatherStationDataset.RAIN):
                value = self._get_base_station_data(sensor_ID)
                break
            if case(WeatherStationDataset.UV):
                value = self._get_base_station_data(sensor_ID)
                break
            if case():
                # at this point only combi sensors may still be under analysis
                if sensor_ID in self._sensor_data:
                    value = self._get_combi_sensor_data(sensor_ID, subsensor_ID)
                else:
                    raise NotExistingError("Invalid sensor")

        return value


    def add_sensor(self, data):
        if isinstance(data, BaseStationSensorData):
            self._sensor_data[WeatherStationDataset.BASE_STATION] = data
        elif isinstance(data, WindSensorData):
            self._sensor_data[WeatherStationDataset.WIND] = data
        elif isinstance(data, CombiSensorData):
            self._sensor_data[data.get_sensor_ID()] = data
        else:
            raise NotExistingError("Invalid oject type for a weather dataset.")


    def remove_sensor(self, sensor_ID):
        del self._sensor_data[sensor_ID]
