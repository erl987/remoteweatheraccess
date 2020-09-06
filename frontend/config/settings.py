import os
from datetime import timedelta

import pytz

# user settings via environment variables
backend_url = os.environ.get('BACKEND_URL', 'localhost')
backend_port = os.environ.get('BACKEND_PORT', 8000)
initial_time_period = timedelta(days=os.environ.get('INITIAL_TIME_PERIOD', 7))
user_time_zone = pytz.timezone(os.environ.get('TIMEZONE', 'Europe/Berlin'))
config_for_plots = {'locale': os.environ.get('LOCALE', 'de')}
default_selected_sensor_ids = ['pressure', 'rain', 'OUT1_temp', 'OUT1_humid']

# application settings
DATA_PROTECTION_POLICY_FILE_PATH = r'text_content/data-protection-policy.md'
IMPRESS_FILE_PATH = r'text_content/impress.md'

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
