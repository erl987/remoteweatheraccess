#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2020 Ralf Rettig (info@personalfme.de)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Run in the most simple way with:
```
cd frontend
gunicorn -b :8050 frontend_app:server
```
"""

import gevent.monkey

gevent.monkey.patch_all()

from functools import partial

import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from frontend_config.settings import *
from frontend_src.backend_proxy import CachedBackendProxy
from frontend_src.cache import cache
from frontend_src.layout import get_layout
from frontend_src.plot import create_figure_config
from frontend_src.utils import convert_input_into_lists, determine_start_and_end_dates

# this app uses the Bootstrap theme United
app = dash.Dash(__name__,
                meta_tags=[
                    {'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}
                ])
app.title = 'Wetterdaten'
server = app.server
cache.init_app(server)
app.layout = partial(get_layout,
                     DATA_PROTECTION_POLICY_FILE_PATH,
                     IMPRESS_FILE_PATH,
                     config_for_plots,
                     default_selected_sensor_ids,
                     initial_time_period,
                     backend_url,
                     backend_port,
                     backend_do_use_https,
                     server)


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

    available_stations, _, available_station_ids = CachedBackendProxy(backend_url,
                                                                      backend_port,
                                                                      backend_do_use_https,
                                                                      server).available_stations()

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

    chosen_sensors, chosen_stations = convert_input_into_lists(chosen_sensors, chosen_stations)
    figure_config = create_figure_config(start_time,
                                         end_time,
                                         chosen_stations,
                                         chosen_sensors,
                                         backend_url,
                                         backend_port,
                                         backend_do_use_https,
                                         server)

    server.logger.info('Updated weather data plot for stations {}, sensors {} in time period \'{}\'-\'{}\''.format(
        chosen_stations,
        chosen_sensors,
        start_time_str,
        end_time_str
    ))
    return figure_config


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
