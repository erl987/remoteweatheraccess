from math import ceil
from typing import Dict, Tuple

from frontend.config.settings import *
from frontend.src.backend_interface import CachedBackend
from frontend.src.utils import floor_to_n, ceil_to_n, get_current_date, update_bounded_index, get_sensor_data


class FigureLayout(object):
    def __init__(self, left_main_axis_pos, right_main_axis_pos, is_empty=False):
        self._figure_layout = {
            'xaxis': {
                'color': GRAPH_FRONT_COLOR,
                'linewidth': DIAGRAM_LINE_WIDTH,
                'gridcolor': GRID_COLOR,
                'tickformatstops': [{
                    'dtickrange': [None, 36000000],
                    'value': '%d.%m.\n%H:%M'
                }, {
                    'dtickrange': [36000000, None],
                    'value': '%a\n%d.%m.%Y'
                }],
                'titlefont': {
                    'family': DIAGRAM_FONT_FAMILY,
                    'size': DIAGRAM_FONT_SIZE
                },
                'tickfont': {
                    'family': DIAGRAM_FONT_FAMILY,
                    'size': DIAGRAM_FONT_SIZE
                },
            },
            'legend': {
                'font': {
                    'family': DIAGRAM_FONT_FAMILY,
                    'color': GRAPH_FRONT_COLOR,
                    'size': DIAGRAM_FONT_SIZE
                },
                'orientation': 'h',
                'xanchor': 'center',
                'y': 1.3,
                'x': 0.5
            },
            'margin': dict(l=20, r=20, t=40, b=100)  # in px
        }

        self._set_x_axis_positions(left_main_axis_pos, right_main_axis_pos)

        if is_empty:
            self._create_empty_plot_axis_layout()

    def get_json(self):
        return dict(self._figure_layout)

    def add_axis(self, sensor_index, color_index, min_max_limits, num_ticks, sensor_description, sensor_id,
                 sensor_unit):
        axis_name = self._get_axis_name(sensor_index)

        self._figure_layout[axis_name] = {
            'title': '{} / {}'.format(sensor_description, sensor_unit),
            'titlefont': {
                'family': DIAGRAM_FONT_FAMILY,
                'color': COLOR_LIST[color_index],
                'size': DIAGRAM_FONT_SIZE
            },
            'tickfont': {
                'family': DIAGRAM_FONT_FAMILY,
                'color': COLOR_LIST[color_index],
                'size': DIAGRAM_FONT_SIZE
            },
            'linecolor': COLOR_LIST[color_index],
            'linewidth': DIAGRAM_LINE_WIDTH,
            'zeroline': False,
            'nticks': num_ticks,
            'range': [min_max_limits[sensor_id]['min'], min_max_limits[sensor_id]['max']]
        }

        return axis_name

    def configure_plot_axis_layout(self, axis_name, left_main_axis_pos, right_main_axis_pos, sensor_index):
        if axis_name not in self._figure_layout:
            raise KeyError('Plot axis \'{}\' is not existing'.format(axis_name))

        if sensor_index == 0:
            self._figure_layout[axis_name]['gridcolor'] = GRID_COLOR
        if sensor_index > 0:
            self._figure_layout[axis_name]['anchor'] = 'free'
            self._figure_layout[axis_name]['overlaying'] = 'y'
            self._figure_layout[axis_name]['showgrid'] = False
        if sensor_index % 2 == 0:
            self._figure_layout[axis_name]['side'] = 'left'
            self._figure_layout[axis_name]['position'] = left_main_axis_pos - sensor_index / 2 * SECONDARY_AXIS_OFFSET
        else:
            self._figure_layout[axis_name]['side'] = 'right'
            self._figure_layout[axis_name]['position'] = right_main_axis_pos + (
                    sensor_index - 1) / 2 * SECONDARY_AXIS_OFFSET

    @staticmethod
    def _get_axis_name(sensor_index):
        if sensor_index == 0:
            axis_name = 'yaxis'
        else:
            axis_name = 'yaxis{}'.format(sensor_index + 1)
        return axis_name

    def _create_empty_plot_axis_layout(self):
        current_date = get_current_date(user_time_zone)

        self._figure_layout['yaxis'] = {
            'title': '',
            'tickfont': {
                'color': GRAPH_FRONT_COLOR,
                'size': DIAGRAM_FONT_SIZE
            },
            'linecolor': GRAPH_FRONT_COLOR,
            'zeroline': False,
            'gridcolor': GRID_COLOR,
            'range': [0, 100]
        }
        self._figure_layout['xaxis']['range'] = [current_date - initial_time_period, current_date]
        self._figure_layout['xaxis']['type'] = 'date'

    def _set_x_axis_positions(self, left_main_axis_pos, right_main_axis_pos):
        self._figure_layout['xaxis']['domain'] = [left_main_axis_pos, right_main_axis_pos]


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


def create_figure_config(start_time, end_time, chosen_stations, chosen_sensors, server):
    data = CachedBackend(backend_url, backend_port, server).data(
        chosen_stations,
        chosen_sensors,
        start_time,
        end_time
    )
    _, all_sensors_data = CachedBackend(backend_url, backend_port, server).available_sensors()

    left_main_axis_pos, right_main_axis_pos, min_max_limits, num_ticks = _determine_plot_axis_setup(
        chosen_stations,
        data,
        chosen_sensors
    )

    plot_data, figure_layout = _create_plot_and_layout_json(
        data,
        all_sensors_data,
        chosen_stations,
        chosen_sensors,
        left_main_axis_pos,
        right_main_axis_pos,
        min_max_limits,
        num_ticks
    )

    figure_config = {
        'data': plot_data,
        'layout': figure_layout
    }

    return figure_config


def _create_plot_and_layout_json(data, all_sensors_data, chosen_stations, chosen_sensors, left_main_axis_pos,
                                 right_main_axis_pos, min_max_limits, num_ticks):
    plot_data = []
    figure_layout = FigureLayout(left_main_axis_pos, right_main_axis_pos)

    color_index = -1
    for sensor_index, sensor_id in enumerate(chosen_sensors):
        color_index = update_bounded_index(color_index, COLOR_LIST)

        sensor_description = all_sensors_data[sensor_id]['description']
        sensor_unit = all_sensors_data[sensor_id]['unit']

        dash_index = -1
        for station_index, station_id in enumerate(chosen_stations):
            dash_index = update_bounded_index(dash_index, DASH_LIST)

            if station_id in data:
                time = data[station_id]['timepoint']
                sensor_data = get_sensor_data(data, station_id, sensor_id)

                if len(sensor_data) > 0:
                    plot_data.append(_create_sensor_plot_data(
                        color_index,
                        dash_index,
                        sensor_data,
                        sensor_description,
                        sensor_index,
                        station_id,
                        time
                    ))
                    axis_name = figure_layout.add_axis(
                        sensor_id,
                        color_index,
                        min_max_limits,
                        num_ticks,
                        sensor_description,
                        sensor_id,
                        sensor_unit
                    )
                    figure_layout.configure_plot_axis_layout(
                        axis_name,
                        left_main_axis_pos,
                        right_main_axis_pos,
                        sensor_index
                    )

    if len(plot_data) == 0:
        figure_layout = FigureLayout(left_main_axis_pos, right_main_axis_pos, is_empty=True)

    return plot_data, figure_layout.get_json()


def _create_sensor_plot_data(color_index, dash_index, sensor_data, sensor_description, sensor_index, station_id, time):
    return {
        'x': time,
        'y': sensor_data,
        'name': '{} - {}'.format(station_id, sensor_description),
        'line': {
            'color': COLOR_LIST[color_index],
            'width': DIAGRAM_LINE_WIDTH,
            'dash': DASH_LIST[dash_index]
        },
        'yaxis': 'y{}'.format(sensor_index + 1),
        'hoverlabel': {
            'namelength': '-1',
            'font': {
                'family': DIAGRAM_FONT_FAMILY,
                'size': DIAGRAM_FONT_SIZE
            }
        }
    }


def _determine_plot_axis_setup(chosen_stations, data, sensors):
    if len(data) > 0 and len(chosen_stations) > 0 and len(sensors) > 0:
        _num_axis_on_left = ceil(len(sensors) / 2)
        _num_axis_on_right = ceil((len(sensors) - 1) / 2)
        left_main_axis_pos = _num_axis_on_left * SECONDARY_AXIS_OFFSET
        right_main_axis_pos = 1 - _num_axis_on_right * SECONDARY_AXIS_OFFSET

        _min_max_sensors = {}
        for sensor_id in sensors:
            _min_data = float('inf')
            _max_data = float('-inf')
            for station_index, station_id in enumerate(chosen_stations):
                if len(data[station_id]) > 0:
                    sensor_data = get_sensor_data(data, station_id, sensor_id)
                    _min_data = min(_min_data, min(sensor_data))
                    _max_data = max(_max_data, max(sensor_data))
            if _min_data != float('inf') and _max_data != float('-inf'):
                _min_max_sensors[sensor_id] = {'min': _min_data, 'max': _max_data}

        if len(_min_max_sensors) > 0:
            num_ticks, min_max_limits = get_scalings(_min_max_sensors)
        else:
            num_ticks = 0
            min_max_limits = None

        return left_main_axis_pos, right_main_axis_pos, min_max_limits, num_ticks
    else:
        return float('inf'), float('inf'), None, 0
