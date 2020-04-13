from remote_weather_access.common import utilities
from remote_weather_access.common.datastructures import CombiSensorData, RainSensorData, BaseStationSensorData


def get_scalings(min_max_sensors):
    """
    Obtains the minimum and maximum scalings of the y-axis for the sensors.

    :param min_max_sensors:     containing the minimum and maximum values of the sensors in the graph.
                                example: {"('baseStation', 'pressure')": {'max': 1018.4, 'min': 1018.4}}
    :type min_max_sensors:      dict(string, dict(string, float))
    :return:                    number of ticks of the y-axis.
    :rtype:                     int
    :return:                    containing the minimum and maximum values for all sensors on the axis.
                                example: {"('baseStation', 'pressure')": {'max': 1018.4, 'min': 1018.4}}
    :rtype:                     dict(string, dict(string, float))
    """
    delta_temp = 5.0  # degree C by definition
    delta_p = 5.0  # hPa by definition
    max_num_ticks = 15

    all_num_ticks = []
    # determine number of ticks
    for key, sensor in min_max_sensors.items():
        if CombiSensorData.TEMPERATURE in key:
            # temperatures should have an identical scaling
            curr_min_temp = utilities.floor_to_n(sensor['min'], delta_temp)
            if 'min_temp' not in locals() or curr_min_temp < min_temp:
                min_temp = curr_min_temp
            curr_max_temp = utilities.ceil_to_n(sensor['max'], delta_temp)
            if 'max_temp' not in locals() or curr_max_temp > max_temp:
                max_temp = curr_max_temp
            all_num_ticks.append(int((max_temp - min_temp) / delta_temp + 1))
        elif RainSensorData.RAIN in key:
            if sensor['max'] < 20:
                delta_rain = 2.5
            elif sensor['max'] < 40:
                delta_rain = 5.0
            elif sensor['max'] < 80:
                delta_rain = 10.0
            elif sensor['max'] < 160:
                delta_rain = 20.0
            else:
                delta_rain = 50.0
            max_rain_counter = utilities.ceil_to_n(sensor['max'], delta_rain)
            all_num_ticks.append(int((max_rain_counter - 0) / delta_rain + 1))
        elif BaseStationSensorData.PRESSURE in key:
            min_p = utilities.floor_to_n(sensor['min'], delta_p)
            max_p = utilities.ceil_to_n(sensor['max'], delta_p)
            all_num_ticks.append(int((max_p - min_p) / delta_p + 1))

    if len(all_num_ticks) == 0:
        all_num_ticks.append(5)  # default value if no special sensors are present

    num_ticks = max(all_num_ticks)
    if num_ticks > max_num_ticks:
        num_ticks = max_num_ticks

    min_max_axis = dict()
    for key, sensor in min_max_sensors.items():
        if CombiSensorData.TEMPERATURE in key:
            # temperature minimum is always the next lower temperature dividable by 5 degree C (already calculated)
            max_temp = min_temp + delta_temp * (num_ticks - 1)
            min_max_axis[key] = {'min': min_temp, 'max': max_temp}
        elif CombiSensorData.HUMIDITY in key:
            # humidity is always in the range from 0 - 100 pct
            min_max_axis[key] = {'min': 0, 'max': 100}
        elif RainSensorData.RAIN in key:
            # rain counter minimum is always 0 mm
            max_rain_counter = 0 + delta_rain * (num_ticks - 1)
            min_max_axis[key] = {'min': 0, 'max': max_rain_counter}
        elif BaseStationSensorData.PRESSURE in key:
            # pressure minimum is always the next lower pressure dividable by 5 hPa (already calculated)
            max_p = min_p + delta_p * (num_ticks - 1)
            min_max_axis[key] = {'min': min_p, 'max': max_p}
        else:
            # all other sensors are scaled by the min/max values
            min_max_axis[key] = {'min': sensor['min'], 'max': sensor['max']}

    return num_ticks, min_max_axis