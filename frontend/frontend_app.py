"""
Run in the most simple way with:
```
cd weatherstation
gunicorn -b :8050 frontend.frontend_app:server
```
"""
import os
from datetime import timedelta
from functools import partial
from math import ceil

import dash
import pytz
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from frontend.src import plot_config
from frontend.src.layout import get_layout
from frontend.src.plot_config import get_current_date
from frontend.src.utils import determine_start_and_end_dates, get_sensor_data, CachedBackend, cache

BACKEND_URL = os.environ.get('BACKEND_URL', 'localhost')
BACKEND_PORT = os.environ.get('BACKEND_PORT', 8000)

data_protection_policy_file_path = r'text_content/data-protection-policy.md'
impress_file_path = r'text_content/impress.md'
initial_time_period = timedelta(days=7)
user_time_zone = pytz.timezone('Europe/Berlin')

config_for_plots = {'locale': 'de'}

default_selected_sensor_ids = ['pressure', 'rain', 'OUT1_temp', 'OUT1_humid']

# color scheme based on that of the Bootstrap theme United
color_list = [
    '#007bff',
    '#38B44A',
    '#DF382C',
    '#868e96',
    '#772953',
    '#E95420',
    '#772953',
    '#e83e8c',
    '#20c997',
    '#17a2b8']

graph_front_color = 'black'
grid_color = '#a5b1cd'
diagram_font_size = 18
diagram_font_family = 'Helvetica Neue, Helvetica, Arial, sans-serif'  # default for Bootstrap
diagram_line_width = 2

# default plot.ly styles
dash_list = ['solid', 'dash', 'dot', 'dashdot']

secondary_axis_offset = 0.1

# this app uses the Bootstrap theme United
app = dash.Dash(__name__,
                meta_tags=[
                    {'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}
                ])
app.title = 'Wetterdaten'
server = app.server
cache.init_app(server)
app.layout = partial(get_layout, data_protection_policy_file_path, impress_file_path, config_for_plots,
                     default_selected_sensor_ids, initial_time_period, BACKEND_URL, BACKEND_PORT, server)

figure_layout = {
    'xaxis': {
        'color': graph_front_color,
        'linewidth': diagram_line_width,
        'gridcolor': grid_color,
        'tickformatstops': [{
            'dtickrange': [None, 36000000],
            'value': '%d.%m.\n%H:%M'
        }, {
            'dtickrange': [36000000, None],
            'value': '%a\n%d.%m.%Y'
        }],
        'titlefont': {
            'family': diagram_font_family,
            'size': diagram_font_size
        },
        'tickfont': {
            'family': diagram_font_family,
            'size': diagram_font_size
        },
    },
    'legend': {
        'font': {
            'family': diagram_font_family,
            'color': graph_front_color,
            'size': diagram_font_size
        },
        'orientation': 'h',
        'xanchor': 'center',
        'y': 1.3,
        'x': 0.5
    },
    'margin': dict(l=20, r=20, t=40, b=100)  # in px
}


@app.callback(
    Output('data-protection-policy-dialog', 'is_open'),
    [Input('open-data-protection-policy', 'n_clicks'), Input('close-data-protection-policy', 'n_clicks')],
    [State('data-protection-policy-dialog', 'is_open')],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output('impress-dialog', 'is_open'),
    [Input('open-impress', 'n_clicks'), Input('close-impress', 'n_clicks')],
    [State('impress-dialog', 'is_open')],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(dash.dependencies.Output('station-dropdown', 'value'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if pathname is None:
        raise PreventUpdate

    provided_station_id = pathname.replace('/', '').upper()

    available_stations, _, available_station_ids = CachedBackend(BACKEND_URL, BACKEND_PORT, server).available_stations()

    if provided_station_id in available_station_ids:
        server.logger.info('Parsed station id \'{}\' from URL'.format(provided_station_id))
        return provided_station_id
    elif len(provided_station_id) == 0:
        server.logger.info('Parsed default station id from URL')
        if len(available_stations) > 0:
            return available_stations[-1]['value']
        else:
            raise PreventUpdate
    else:
        server.logger.error('Parsed invalid station id from URL')
        raise PreventUpdate


@app.callback(
    Output('station-data-tab', 'active_tab'),
    [Input(component_id='station-dropdown', component_property='value')]
)
def select_station_info_tab(chosen_stations):
    if isinstance(chosen_stations, str):
        chosen_stations = [chosen_stations]

    if chosen_stations and len(chosen_stations) > 0:
        open_tab_id = chosen_stations[0]
    else:
        open_tab_id = ''

    return open_tab_id


@app.callback(
    Output('weather-data-graph', 'figure'),
    [Input(component_id='time-period-picker', component_property='start_date'),
     Input(component_id='time-period-picker', component_property='end_date'),
     Input(component_id='station-dropdown', component_property='value'),
     Input(component_id='sensor-dropdown', component_property='value')]
)
def update_weather_plot(start_time_str, end_time_str, chosen_stations, chosen_sensors):
    start_time, end_time = determine_start_and_end_dates(start_time_str, end_time_str)
    if start_time is None or end_time is None or end_time < start_time:
        raise PreventUpdate

    if isinstance(chosen_stations, str):
        chosen_stations = [chosen_stations]
    if isinstance(chosen_sensors, str):
        chosen_sensors = [chosen_sensors]

    if 'range' in figure_layout['xaxis']:
        del figure_layout['xaxis']['range']
    if 'type' in figure_layout['xaxis']:
        del figure_layout['xaxis']['type']
    data = CachedBackend(BACKEND_URL, BACKEND_PORT, server).data(chosen_stations, chosen_sensors, start_time, end_time)
    left_main_axis_pos, right_main_axis_pos, min_max_limits, num_ticks = determine_plot_axis_setup(chosen_stations,
                                                                                                   data, chosen_sensors)

    _, all_sensors_data = CachedBackend(BACKEND_URL, BACKEND_PORT, server).available_sensors()

    plot_data = []
    color_index = -1
    for sensor_index, sensor_id in enumerate(chosen_sensors):
        color_index += 1
        if color_index >= len(color_list):
            color_index = 0

        sensor_description = all_sensors_data[sensor_id]['description']
        sensor_unit = all_sensors_data[sensor_id]['unit']
        dash_index = -1
        for station_index, station_id in enumerate(chosen_stations):
            dash_index += 1
            if dash_index >= len(dash_list):
                dash_index = 0

            if station_id in data:
                time = data[station_id]['timepoint']
                sensor_data = get_sensor_data(data, station_id, sensor_id)
                if len(sensor_data) > 0:
                    plot_data.append(create_sensor_plot_data(color_index, dash_index, sensor_data, sensor_description,
                                                             sensor_index, station_id, time))

                    if sensor_index == 0:
                        axis_name = 'yaxis'
                    else:
                        axis_name = 'yaxis{}'.format(sensor_index + 1)
                    figure_layout[axis_name] = create_plot_axis_layout(color_index, min_max_limits, num_ticks,
                                                                       sensor_description, sensor_id, sensor_unit)
                    configure_plot_axis_layout(axis_name, left_main_axis_pos, right_main_axis_pos, sensor_index)

    if len(plot_data) == 0:
        create_empty_plot_axis_layout()

    figure_config = {
        'data': plot_data,
        'layout': figure_layout
    }

    server.logger.info('Updated weather data plot for stations {}, sensors {} in time period \'{}\'-\'{}\''.format(
        chosen_stations,
        chosen_sensors,
        start_time_str,
        end_time_str
    ))
    return figure_config


def create_empty_plot_axis_layout():
    current_date = get_current_date(user_time_zone)

    figure_layout['yaxis'] = {
        'title': '',
        'tickfont': {
            'color': graph_front_color,
            'size': diagram_font_size
        },
        'linecolor': graph_front_color,
        'zeroline': False,
        'gridcolor': grid_color,
        'range': [0, 100]
    }
    figure_layout['xaxis']['range'] = [current_date - initial_time_period, current_date]
    figure_layout['xaxis']['type'] = 'date'


def create_sensor_plot_data(color_index, dash_index, sensor_data, sensor_description, sensor_index, station_id, time):
    return {'x': time,
            'y': sensor_data,
            'name': '{} - {}'.format(station_id, sensor_description),
            'line': {
                'color': color_list[color_index],
                'width': diagram_line_width,
                'dash': dash_list[dash_index]
            },
            'yaxis': 'y{}'.format(sensor_index + 1),
            'hoverlabel': {
                'namelength': '-1',
                'font': {
                    'family': diagram_font_family,
                    'size': diagram_font_size
                }
            }
            }


def configure_plot_axis_layout(axis_name, left_main_axis_pos, right_main_axis_pos, sensor_index):
    if sensor_index == 0:
        figure_layout[axis_name]['gridcolor'] = grid_color
    if sensor_index > 0:
        figure_layout[axis_name]['anchor'] = 'free'
        figure_layout[axis_name]['overlaying'] = 'y'
        figure_layout[axis_name]['showgrid'] = False
    if sensor_index % 2 == 0:
        figure_layout[axis_name]['side'] = 'left'
        figure_layout[axis_name]['position'] = left_main_axis_pos - sensor_index / 2 * secondary_axis_offset
    else:
        figure_layout[axis_name]['side'] = 'right'
        figure_layout[axis_name]['position'] = right_main_axis_pos + (sensor_index - 1) / 2 * secondary_axis_offset


def create_plot_axis_layout(color_index, min_max_limits, num_ticks, sensor_description, sensor_id, sensor_unit):
    return {
        'title': '{} / {}'.format(sensor_description, sensor_unit),
        'titlefont': {
            'family': diagram_font_family,
            'color': color_list[color_index],
            'size': diagram_font_size
        },
        'tickfont': {
            'family': diagram_font_family,
            'color': color_list[color_index],
            'size': diagram_font_size
        },
        'linecolor': color_list[color_index],
        'linewidth': diagram_line_width,
        'zeroline': False,
        'nticks': num_ticks,
        'range': [min_max_limits[sensor_id]['min'], min_max_limits[sensor_id]['max']]
    }


def determine_plot_axis_setup(chosen_stations, data, sensors):
    if len(data) > 0 and len(chosen_stations) > 0 and len(sensors) > 0:
        _num_axis_on_left = ceil(len(sensors) / 2)
        _num_axis_on_right = ceil((len(sensors) - 1) / 2)
        left_main_axis_pos = _num_axis_on_left * secondary_axis_offset
        right_main_axis_pos = 1 - _num_axis_on_right * secondary_axis_offset

        figure_layout['xaxis']['domain'] = [left_main_axis_pos, right_main_axis_pos]

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
            num_ticks, min_max_limits = plot_config.get_scalings(_min_max_sensors)
        else:
            num_ticks = 0
            min_max_limits = None

        return left_main_axis_pos, right_main_axis_pos, min_max_limits, num_ticks
    else:
        return float('inf'), float('inf'), None, 0


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
