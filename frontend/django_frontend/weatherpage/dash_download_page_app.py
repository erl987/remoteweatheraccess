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

from locale import setlocale, LC_ALL
from logging import getLogger
from os import environ

from cacheout import Cache
from dash import Output, Input, State, ALL
from django_plotly_dash import DjangoDash
from google.cloud.storage import Bucket

from frontend.django_frontend.weatherpage.dash_download_page.callback import update_downloadable_data_callback, \
    download_data_callback
from frontend.django_frontend.weatherpage.dash_download_page.dash_settings import AVAILABLE_DATA_CACHE_TIMEOUT_IN_SEC, \
    EXPORTER_BUCKET_NAME
from frontend.django_frontend.weatherpage.dash_download_page.layout import get_layout
from frontend.django_frontend.weatherpage.dash_download_page.utils import get_storage_client, is_deployed_environment

logger = getLogger('django')

app = DjangoDash('dash-download')
data_cache = Cache(ttl=int(AVAILABLE_DATA_CACHE_TIMEOUT_IN_SEC))

if is_deployed_environment():
    setlocale(LC_ALL, environ['LANGUAGE_CODE'])
    bucket = Bucket(get_storage_client(), EXPORTER_BUCKET_NAME)
else:
    bucket = None

app.layout = get_layout(data_cache, bucket)


@app.callback(
    [Output('data-downloader', 'data'),
     Output('no-month-selected-warning', 'is_open'),
     Output('download-error', 'is_open')],
    Input('download-button', 'n_clicks'),
    State('station-dropdown', 'value'),
    State('year-dropdown', 'value'),
    State({'type': 'month-checkbox', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def download_data(_, station_label, year, chosen_months_in_year):
    return download_data_callback(chosen_months_in_year, station_label, year, data_cache, bucket)


@app.callback(
    [Output('downloadable-station-data', 'children'),
     Output('initialize-error', 'is_open')],
    Input('station-dropdown', 'value'),
    Input('year-dropdown', 'value')
)
def update_downloadable_data(station_label, year):
    return update_downloadable_data_callback(station_label, year, data_cache, bucket)
