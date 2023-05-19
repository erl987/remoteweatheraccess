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

from dash import dcc, html
from dash_bootstrap_components import Card, Tab, Col, Label, Input, Tabs, Row
from dash_breakpoints import WindowBreakpoints
from dateutil.parser import parse

from .backend_proxy import CachedBackendProxy
from .utils import BootstrapBreakpoint, BREAKPOINT_WIDTH_IN_PX

logger = getLogger('django')


def get_configuration_from_backend(backend_url, backend_port, do_use_https):
    cached_backend = CachedBackendProxy(backend_url, backend_port, do_use_https)

    first_time, last_time = cached_backend.time_limits()
    available_sensors, available_sensors_data = cached_backend.available_sensors()
    available_stations, available_stations_data, _ = cached_backend.available_stations()

    return first_time, last_time, available_stations, available_sensors, available_stations_data


def get_date_picker_card(first_time, last_time, initial_time_period):
    if first_time and last_time:
        date_picker = dcc.DatePickerRange(
            id='time-period-picker',
            min_date_allowed=first_time,
            max_date_allowed=last_time,
            start_date=parse(last_time) - initial_time_period,
            end_date=last_time,
            display_format='DD.MM.YYYY',
            stay_open_on_select=True,
            start_date_placeholder_text='Startdatum',
            end_date_placeholder_text='Enddatum',
            first_day_of_week=1
        )
    else:
        date_picker = dcc.DatePickerRange(
            id='time-period-picker',
            disabled=True,
            start_date_placeholder_text='Startdatum',
            end_date_placeholder_text='Enddatum'
        )

    return Card(
        [
            html.H2('Zeitraum'),
            html.Div(date_picker)
        ],
        body=True,
        className='p-1'
    )


def get_sensor_dropdown_card(available_sensors, default_selected_sensor_ids):
    return Card(
        [
            html.H2('Sensoren'),
            html.Div(
                dcc.Dropdown(
                    id='sensor-dropdown',
                    placeholder='Auswählen ...',
                    options=available_sensors,
                    value=default_selected_sensor_ids,
                    searchable=False,
                    multi=True
                )
            )
        ],
        body=True,
        className='p-1'
    )


def get_station_dropdown_card(available_stations):
    if len(available_stations) > 0:
        selected_station = available_stations[-1]['value']
    else:
        selected_station = None

    return Card(
        [
            html.H2('Stationen'),
            html.Div(
                dcc.Dropdown(
                    id='station-dropdown',
                    placeholder='Auswählen ...',
                    options=available_stations,
                    value=selected_station,
                    searchable=False,
                    multi=True
                )
            )

        ],
        body=True,
        className='p-1'
    )


def get_station_info_tabs(available_stations_data):
    station_info_tabs = []

    for station in available_stations_data:
        curr_station_id = station['station_id']
        splitted_location_info = station['location'].split('/')
        station_town = splitted_location_info[0]
        if station['latitude'] > 0:
            latitude_str = '{}\N{DEGREE SIGN} N'.format(station['latitude'])
        else:
            latitude_str = '{}\N{DEGREE SIGN} S'.format(station['latitude'])
        if station['longitude'] > 0:
            longitude_str = '{}\N{DEGREE SIGN} O'.format(station['longitude'])
        else:
            longitude_str = '{}\N{DEGREE SIGN} W'.format(station['longitude'])

        station_info_tabs.append(
            Tab([
                Row(
                    Col([
                        Label('Standort', html_for='location_info_{}'.format(curr_station_id)),
                        Input(id='location_info_{}'.format(curr_station_id),
                              placeholder=station['location'],
                              disabled=True)
                    ])),
                Row(
                    Col([
                        Label('Höhe', html_for='height_info_{}'.format(curr_station_id)),
                        Input(id='height_info_{}'.format(curr_station_id),
                              placeholder='{} m'.format(station['height']),
                              disabled=True)

                    ])),
                Row(
                    Col([
                        Label('Koordinaten', html_for='coordinates_info_{}'.format(curr_station_id)),
                        Input(id='coordinates_info_{}'.format(curr_station_id),
                              placeholder='{} / {}'.format(latitude_str, longitude_str),
                              disabled=True)
                    ])),
                Row(
                    Col([
                        Label('Wetterstation', html_for='device_info_{}'.format(curr_station_id)),
                        Input(id='device_info_{}'.format(curr_station_id),
                              placeholder=station['device'],
                              disabled=True)
                    ]))],
                label=station_town,
                tab_id=curr_station_id
            )
        )

    return station_info_tabs


def get_station_data_card(available_stations_data):
    return Card([
        html.H2('Stationsdaten'),
        Tabs(
            get_station_info_tabs(available_stations_data),
            id='station-data-tab'
        )],
        body=True,
        className='p-1'
    )


def get_layout(config_for_plots, default_selected_sensor_ids, initial_time_period, backend_url, backend_port,
               backend_do_use_https):
    first_time, last_time, available_stations, available_sensors, available_stations_data = \
        get_configuration_from_backend(backend_url, backend_port, backend_do_use_https)

    logger.info('Created and provided new layout')

    return Row(
        [
            dcc.Location(id='url', refresh=True),

            dcc.Store(id='breakpoint-memory'),

            dcc.Store(id='is-init-memory'),

            WindowBreakpoints(
                id="breakpoints",
                widthBreakpointThresholdsPx=[
                    BREAKPOINT_WIDTH_IN_PX[BootstrapBreakpoint.SM] - 1,
                    BREAKPOINT_WIDTH_IN_PX[BootstrapBreakpoint.MD] - 1,
                    BREAKPOINT_WIDTH_IN_PX[BootstrapBreakpoint.LG] - 1,
                    BREAKPOINT_WIDTH_IN_PX[BootstrapBreakpoint.XL] - 1,
                    BREAKPOINT_WIDTH_IN_PX[BootstrapBreakpoint.XXL] - 1
                ],
                widthBreakpointNames=[
                    BootstrapBreakpoint.XS.name.lower(),
                    BootstrapBreakpoint.SM.name.lower(),
                    BootstrapBreakpoint.MD.name.lower(),
                    BootstrapBreakpoint.LG.name.lower(),
                    BootstrapBreakpoint.XL.name.lower(),
                    BootstrapBreakpoint.XXL.name.lower()
                ]
            ),

            Col(
                id='configuration',
                children=[
                    get_date_picker_card(first_time, last_time, initial_time_period),
                    get_sensor_dropdown_card(available_sensors, default_selected_sensor_ids),
                    get_station_dropdown_card(available_stations),
                    get_station_data_card(available_stations_data)
                ],
                width=12,
                lg=4
            ),

            Col(
                dcc.Loading(
                    id='weather-data-graph-loading',
                    children=[dcc.Graph(id='weather-data-graph', config=config_for_plots, className='diagram',
                                        responsive=True, style={'height': '100vh', 'max-height': '600px'})],
                    type='circle'
                ),
                width=12,
                lg=8
            )
        ]
    )
