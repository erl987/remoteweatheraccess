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

import os
from datetime import timedelta

import pytz

# user settings via environment variables
backend_url = os.environ.get('BACKEND_URL', 'localhost')
backend_port = os.environ.get('BACKEND_PORT', 8000)
backend_do_use_https = os.environ.get('BACKEND_DO_USE_HTTPS', 'false').lower() != 'false'
initial_time_period = timedelta(days=os.environ.get('INITIAL_TIME_PERIOD', 7))
user_time_zone = pytz.timezone(os.environ.get('TIMEZONE', 'Europe/Berlin'))
config_for_plots = {'locale': os.environ.get('LOCALE', 'de')}
default_selected_sensor_ids = ['pressure', 'rain', 'OUT1_temp', 'OUT1_humid']
brand_name = os.environ.get('BRAND_NAME', 'Das Wetternetzwerk')

# these files need to be provided locally
data_protection_policy_file_path = r'text_content/data-protection-policy.md'
impress_file_path = r'text_content/impress.md'

# application settings

# color scheme based on that of the Bootstrap theme United
COLOR_LIST = [
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

GRAPH_FRONT_COLOR = 'black'
GRID_COLOR = '#a5b1cd'
DIAGRAM_FONT_SIZE = 18
DIAGRAM_FONT_FAMILY = 'Helvetica Neue, Helvetica, Arial, sans-serif'  # default for Bootstrap
DIAGRAM_LINE_WIDTH = 2
DASH_LIST = ['solid', 'dash', 'dot', 'dashdot']  # default plot.ly styles

SECONDARY_AXIS_OFFSET = 0.1
