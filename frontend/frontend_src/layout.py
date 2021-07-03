#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2021 Ralf Rettig (info@personalfme.de)
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
import os

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dateutil.parser import parse

from frontend_config.settings import brand_name
from . import dash_reusable_components as drc
from .backend_proxy import CachedBackendProxy


def get_configuration_from_backend(backend_url, backend_port, do_use_https, app):
    cached_backend = CachedBackendProxy(backend_url, backend_port, do_use_https, app)

    first_time, last_time = cached_backend.time_limits()
    available_sensors, available_sensors_data = cached_backend.available_sensors()
    available_stations, available_stations_data, _ = cached_backend.available_stations()

    return first_time, last_time, available_stations, available_sensors, available_stations_data


def get_navbar_component():
    return dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink('Home', href='')),
            dbc.NavItem(dbc.NavLink('Datenschutz', href='#', id='open-data-protection-policy')),
            dbc.NavItem(dbc.NavLink('Impressum', href='#', id='open-impress'))
        ],
        brand=brand_name,
        brand_href='',
        color='primary',
        dark=True,
        fluid=True,
        expand='lg'
    )


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

    return dbc.Card(
        [
            html.H2('Zeitraum'),
            html.Div(date_picker)
        ], body=True
    )


def get_sensor_dropdown_card(available_sensors, default_selected_sensor_ids):
    return dbc.Card(
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
        ], body=True
    )


def get_station_dropdown_card(available_stations):
    if len(available_stations) > 0:
        selected_station = available_stations[-1]['value']
    else:
        selected_station = None

    return dbc.Card(
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

        ], body=True
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
            dbc.Tab(
                dbc.Col([
                    dbc.FormGroup([
                        dbc.Label('Standort', html_for='location_info_{}'.format(curr_station_id)),
                        dbc.Input(id='location_info_{}'.format(curr_station_id),
                                  placeholder=station['location'],
                                  disabled=True)
                    ]),
                    dbc.FormGroup([
                        dbc.Label('Höhe', html_for='height_info_{}'.format(curr_station_id)),
                        dbc.Input(id='height_info_{}'.format(curr_station_id),
                                  placeholder='{} m'.format(station['height']),
                                  disabled=True)

                    ]),
                    dbc.FormGroup([
                        dbc.Label('Koordinaten', html_for='coordinates_info_{}'.format(curr_station_id)),
                        dbc.Input(id='coordinates_info_{}'.format(curr_station_id),
                                  placeholder='{} / {}'.format(latitude_str, longitude_str),
                                  disabled=True)
                    ]),
                    dbc.FormGroup([
                        dbc.Label('Wetterstation', html_for='device_info_{}'.format(curr_station_id)),
                        dbc.Input(id='device_info_{}'.format(curr_station_id),
                                  placeholder=station['device'],
                                  disabled=True)
                    ])
                ]),
                label=station_town,
                tab_id=curr_station_id
            )
        )

    return station_info_tabs


def get_station_data_card(available_stations_data):
    return dbc.Card([
        html.H2('Stationsdaten'),
        dbc.Tabs(
            get_station_info_tabs(available_stations_data),
            id='station-data-tab'
        )
    ], body=True)


def get_layout(data_protection_policy_file_path, impress_file_path, config_for_plots, default_selected_sensor_ids,
               initial_time_period, backend_url, backend_port, backend_do_use_https, app):
    first_time, last_time, available_stations, available_sensors, available_stations_data = \
        get_configuration_from_backend(backend_url, backend_port, backend_do_use_https, app)

    cached_backend = CachedBackendProxy(backend_url, backend_port, backend_do_use_https, app)

    if os.path.exists(data_protection_policy_file_path):
        data_protection_policy_text = cached_backend.get_text_file_content(data_protection_policy_file_path)
    else:
        app.logger.warn('File containing the data protection policy not found: {}'
                        .format(data_protection_policy_file_path))
        data_protection_policy_text = 'File containing the data protection policy not found'

    if os.path.exists(impress_file_path):
        impress_text = cached_backend.get_text_file_content(impress_file_path)
    else:
        app.logger.warn('File containing the impress not found: {}'.format(impress_file_path))
        impress_text = 'File containing the impress not found'

    app.logger.info('Created and provided new layout')

    return dbc.Container(
        fluid=True,
        children=[
            dcc.Location(id='url', refresh=True),

            drc.ModalDialog(
                the_id='data-protection-policy',
                dialog_content=data_protection_policy_text
            ),

            drc.ModalDialog(
                the_id='impress',
                dialog_content=impress_text
            ),

            dbc.Row(
                [
                    dbc.Col(
                        get_navbar_component(),
                        width=12
                    )
                ]
            ),

            dbc.Row(
                [
                    dbc.Col(
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

                    dbc.Col(
                        dbc.Spinner(dcc.Graph(id='weather-data-graph', config=config_for_plots, className='diagram')),
                        width='auto',
                        lg=8,
                        style={'minWidth': '800px'}
                    )
                ]
            ),

            dbc.Row(
                [dbc.Col(
                    html.P(children='Copyright (C) 2021 Ralf Rettig'),
                    width=12
                )]
            )
        ]
    )
