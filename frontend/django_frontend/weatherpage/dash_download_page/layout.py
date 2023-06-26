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

from calendar import month_name
from logging import getLogger

import dash_bootstrap_components as dbc
from dash import html, dcc

from .storage import get_available_data
from .utils import get_station_id, get_station_label_info_from_backend

logger = getLogger('django')


def get_layout(data_cache, bucket):
    logger.info('Creating layout')
    available_data = get_available_data(data_cache, bucket)
    station_label_info, station_labels = _get_station_labels(available_data)
    default_station_label, default_station_id = _get_default_station(station_labels, station_label_info)
    default_year, years_for_default_station = _get_default_year(available_data, default_station_id)

    return html.Div([
        dbc.Alert('Es wurden keine Monate ausgewählt.', id='no-month-selected-warning', color='warning',
                  dismissable=True, is_open=False),
        dbc.Alert('Der Download ist fehlgeschlagen. Versuchen Sie es später noch einmal.', id='download-error',
                  color='danger', dismissable=True, is_open=False),
        dbc.Alert('Fehler beim Herunterladen der verfügbaren Dateien. Versuchen Sie es später noch einmal.',
                  id='initialize-error', color='danger', dismissable=False, is_open=False),
        html.Div([
            dbc.Row([
                dbc.Col(html.P('Station:'), className='col-md-1 col-sm-2 mt-1'),
                dbc.Col(dcc.Dropdown(station_labels, default_station_label, id='station-dropdown',
                                     clearable=False, searchable=False),
                        className='col-md-2 col-sm-6')
            ], className='justify-content-md-begin'),
            dbc.Row([
                dbc.Col(html.P('Jahr:'), className='col-md-1 col-sm-2 mt-1'),
                dbc.Col(dcc.Dropdown(years_for_default_station, default_year, id='year-dropdown',
                                     clearable=False, searchable=False),
                        className='col-md-2 col-sm-6')
            ], className='justify-content-md-begin'),
            dbc.Row(dbc.Col(html.H2('Verfügbare Daten'), className='col-md-auto mt-4 mb-1'),
                    className='justify-content-md-begin'),
            dbc.Row(dbc.Col(html.Div(id='downloadable-station-data'), className='col-md-12')),
            dbc.Row(dbc.Col(html.P('Die heruntergeladenen Dateien werden im Standard-Downloadverzeichnis gespeichert.'),
                            className='col-md-auto'), className='justify-content-md-begin mt-4'),
            dbc.Row(dbc.Col(dbc.Button('Herunterladen', id='download-button'), className='col-md-2'),
                    className='justify-content-md-begin mt-3'),
            dcc.Download(id='data-downloader'),
        ], className='m-4')
    ])


def _get_station_labels(available_data):
    station_label_info_from_backend = get_station_label_info_from_backend()
    station_ids_with_data_files = _get_station_ids(available_data)

    station_labels = []
    for station_id, station_label in station_label_info_from_backend.items():
        if station_id in station_ids_with_data_files:
            station_labels.append(station_label)

    if len(station_labels) != len(station_ids_with_data_files):
        raise AssertionError('Not all stations with export data files have metadata in the backend database')

    return station_label_info_from_backend, sorted(station_labels)


def _get_default_year(available_data, default_station_id):
    if not default_station_id:
        return None, None

    years_for_default_station = sorted(list(available_data[default_station_id].keys()))

    if len(years_for_default_station) > 0:
        default_year = years_for_default_station[-1]
    else:
        default_year = None

    return default_year, years_for_default_station


def _get_default_station(station_labels, station_label_info):
    if len(station_labels) > 0:
        default_station_label = station_labels[0]
        default_station_id = get_station_id(default_station_label, station_label_info)
    else:
        default_station_label = None
        default_station_id = None

    return default_station_label, default_station_id


def _get_station_ids(available_data):
    return set(available_data.keys())


def get_calendar_for_year(available_data, station_id, year):
    _NUM_MONTHS_PER_ROW = 4

    if year in available_data[station_id]:
        months_with_data = [item[0] for item in available_data[station_id][year]]
    else:
        months_with_data = []

    month_components = []
    for month in range(1, 12 + 1):
        is_disabled = month not in months_with_data
        month_components.append(dbc.Col(dbc.Checkbox(label=month_name[month],
                                                     value=not is_disabled,
                                                     disabled=is_disabled,
                                                     id={'type': 'month-checkbox', 'index': month}),
                                        className='col-md-3 col-sm-6 col-6'))

    components = []
    for i in range(0, 12, _NUM_MONTHS_PER_ROW):
        row = month_components[i: i + _NUM_MONTHS_PER_ROW]
        components.append(dbc.Row(row))

    return html.Div(components)
