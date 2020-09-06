from datetime import datetime
from typing import Dict, Tuple

from frontend.src.utils import floor_to_n, ceil_to_n


def get_scalings(min_max_sensors: Dict[str, Dict[str, float]]) -> Tuple[int, Dict[str, Dict[str, float]]]:
    """
    Obtains the minimum and maximum scalings of the y-axis for the sensors.

    :param min_max_sensors:     containing the minimum and maximum values of the sensors in the graph
    :return:                    number of ticks of the y-axis.
    :return:                    containing the minimum and maximum values for all sensors on the axis
    """
    delta_temp = 5.0  # degree C by definition
    delta_p = 5.0  # hPa by definition
    max_num_ticks = 15

    delta_rain = 0.0
    min_p = 0.0
    min_temp = float('inf')
    max_temp = float('-inf')

    all_num_ticks = []
    # determine number of ticks
    for key, sensor in min_max_sensors.items():
        if 'temperature' in key:
            # temperatures should have an identical scaling
            curr_min_temp = floor_to_n(sensor['min'], delta_temp)
            if curr_min_temp < min_temp:
                min_temp = curr_min_temp
            curr_max_temp = ceil_to_n(sensor['max'], delta_temp)
            if curr_max_temp > max_temp:
                max_temp = curr_max_temp
            all_num_ticks.append(int((max_temp - min_temp) / delta_temp + 1))
        elif 'rain' in key:
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
            max_rain_counter = ceil_to_n(sensor['max'], delta_rain)
            all_num_ticks.append(int((max_rain_counter - 0) / delta_rain + 1))
        elif 'pressure' in key:
            min_p = floor_to_n(sensor['min'], delta_p)
            max_p = ceil_to_n(sensor['max'], delta_p)
            all_num_ticks.append(int((max_p - min_p) / delta_p + 1))

    if len(all_num_ticks) == 0:
        all_num_ticks.append(5)  # default value if no special sensors are present

    num_ticks = max(all_num_ticks)
    if num_ticks > max_num_ticks:
        num_ticks = max_num_ticks

    min_max_axis = _get_min_max_axis(delta_p, delta_rain, delta_temp, min_max_sensors, min_p, min_temp, num_ticks)

    return num_ticks, min_max_axis


def _get_min_max_axis(delta_p, delta_rain, delta_temp, min_max_sensors, min_p, min_temp, num_ticks):
    min_max_axis = dict()
    for key, sensor in min_max_sensors.items():
        if 'temperature' in key:
            # temperature minimum is always the next lower temperature dividable by 5 degree C (already calculated)
            max_temp = min_temp + delta_temp * (num_ticks - 1)
            min_max_axis[key] = {'min': min_temp, 'max': max_temp}
        elif 'humidity' in key:
            # humidity is always in the range from 0 - 100 pct
            min_max_axis[key] = {'min': 0, 'max': 100}
        elif 'rain' in key:
            # rain counter minimum is always 0 mm
            max_rain_counter = 0 + delta_rain * (num_ticks - 1)
            min_max_axis[key] = {'min': 0, 'max': max_rain_counter}
        elif 'pressure' in key:
            # pressure minimum is always the next lower pressure dividable by 5 hPa (already calculated)
            max_p = min_p + delta_p * (num_ticks - 1)
            min_max_axis[key] = {'min': min_p, 'max': max_p}
        else:
            # all other sensors are scaled by the min/max values
            min_max_axis[key] = {'min': sensor['min'], 'max': sensor['max']}

    return min_max_axis


def get_current_date(user_time_zone):
    return datetime.now(user_time_zone).date()
