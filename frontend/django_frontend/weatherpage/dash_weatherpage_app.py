#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2023 Ralf Rettig (info@personalfme.de)
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

from logging import getLogger

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from django_plotly_dash import DjangoDash

from frontend.django_frontend.weatherpage.dash_weatherpage.dash_settings import CONFIG_FOR_PLOTS, \
    DEFAULT_SELECTED_SENSOR_IDS_LARGE_SCREEN, INITIAL_TIME_PERIOD, \
    BACKEND_URL, BACKEND_PORT, BACKEND_DO_USE_HTTPS, DEFAULT_SELECTED_SENSOR_IDS_SMALL_SCREEN
from .dash_weatherpage.backend_proxy import CachedBackendProxy
from .dash_weatherpage.layout import get_layout
from .dash_weatherpage.plot import create_figure_config, patch_figure_for_breakpoint
from .dash_weatherpage.utils import convert_input_into_lists, determine_start_and_end_dates, \
    is_at_least_bootstrap_breakpoint, BootstrapBreakpoint

plotly_de_locale = 'https://cdn.plot.ly/plotly-locale-de-2.1.0.js'
app = DjangoDash("dash-frontend",
                 external_scripts=[plotly_de_locale])
app.title = 'Wetterdaten'
app.layout = get_layout(CONFIG_FOR_PLOTS,
                        DEFAULT_SELECTED_SENSOR_IDS_LARGE_SCREEN,
                        INITIAL_TIME_PERIOD,
                        BACKEND_URL,
                        BACKEND_PORT,
                        BACKEND_DO_USE_HTTPS)

logger = getLogger('django')

app.clientside_callback(
    """
    function(wBreakpoint) {
        return wBreakpoint;
    }
    """,
    Output(component_id='breakpoint-memory', component_property='data'),
    Input(component_id='breakpoints', component_property='widthBreakpoint'),
)


@app.callback(Output(component_id='station-dropdown', component_property='value'),
              [Input(component_id='url', component_property='pathname')])
def display_page(pathname):
    if pathname is None:
        raise PreventUpdate

    provided_station_id = pathname.replace('/', '').upper()

    __, _, available_station_ids = CachedBackendProxy(BACKEND_URL,
                                                      BACKEND_PORT,
                                                      BACKEND_DO_USE_HTTPS).available_stations()

    if provided_station_id in available_station_ids:
        logger.info('Parsed station id \'{}\' from URL'.format(provided_station_id))
        return provided_station_id
    elif len(provided_station_id) == 0:
        logger.info('Parsed default station id from URL')
        if len(available_station_ids) > 0:
            return available_station_ids[-1]
        else:
            raise PreventUpdate
    else:
        logger.error('Parsed invalid station id from URL')
        raise PreventUpdate


@app.callback(
    Output(component_id='station-data-tab', component_property='active_tab'),
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
    Output(component_id='sensor-dropdown', component_property='value'),
    [Input(component_id='breakpoint-memory', component_property='data'),
     State(component_id='sensor-dropdown', component_property='value'),
     State(component_id='is-init-memory', component_property='data')]
)
def initialize_selected_sensors(breakpoint_name, chosen_sensors, is_initialized):
    if is_initialized:
        return chosen_sensors
    else:
        if not breakpoint_name or is_at_least_bootstrap_breakpoint(breakpoint_name, BootstrapBreakpoint.SM):
            return DEFAULT_SELECTED_SENSOR_IDS_LARGE_SCREEN
        else:
            return DEFAULT_SELECTED_SENSOR_IDS_SMALL_SCREEN


@app.callback(
    [Output(component_id='weather-data-graph', component_property='figure'),
     Output(component_id='is-init-memory', component_property='data')],
    [Input(component_id='time-period-picker', component_property='start_date'),
     Input(component_id='time-period-picker', component_property='end_date'),
     Input(component_id='station-dropdown', component_property='value'),
     Input(component_id='sensor-dropdown', component_property='value'),
     Input(component_id='breakpoint-memory', component_property='data'),
     State(component_id='is-init-memory', component_property='data')]
)
def update_weather_plot(start_time_str, end_time_str, chosen_stations, chosen_sensors, breakpoint_name, is_initialized,
                        **kwargs):
    if not breakpoint_name:
        logger.warning('No breakpoint information available, assuming the largest one')

    triggered_id = kwargs["callback_context"].triggered[0]['prop_id']

    if is_initialized and triggered_id == 'breakpoint-memory.data':
        return patch_figure_for_breakpoint(breakpoint_name, chosen_sensors), True
    else:
        start_time, end_time = determine_start_and_end_dates(start_time_str, end_time_str)
        if start_time is None or end_time is None or end_time < start_time:
            raise PreventUpdate

        chosen_sensors, chosen_stations = convert_input_into_lists(chosen_sensors, chosen_stations)
        plot_data, figure_layout = create_figure_config(start_time,
                                                        end_time,
                                                        chosen_stations,
                                                        chosen_sensors,
                                                        breakpoint_name,
                                                        BACKEND_URL,
                                                        BACKEND_PORT,
                                                        BACKEND_DO_USE_HTTPS)

        logger.info('Updated weather data plot for stations {}, sensors {} in time period \'{}\'-\'{}\''.format(
            chosen_stations,
            chosen_sensors,
            start_time_str,
            end_time_str
        ))

        return {
            'data': plot_data,
            'layout': figure_layout
        }, True
