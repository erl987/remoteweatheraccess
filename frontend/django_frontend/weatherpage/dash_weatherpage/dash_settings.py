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

from datetime import timedelta
from os import environ

from pytz import timezone

from .utils import BootstrapBreakpoint, BREAKPOINT_WIDTH_IN_PX, backend_uses_https

# user settings via environment variables
BACKEND_URL = environ['BACKEND_URL']
BACKEND_PORT = int(environ['BACKEND_PORT'])
BACKEND_DO_USE_HTTPS = backend_uses_https()
INITIAL_TIME_PERIOD = timedelta(days=int(environ['INITIAL_TIME_PERIOD']))
USER_TIME_ZONE = timezone(environ['USER_TIME_ZONE'])
CONFIG_FOR_PLOTS = {'locale': environ['LANGUAGE_CODE'].split('_')[0],
                    'modeBarButtonsToAdd': ['v1hovermode', 'toggleSpikelines']}

DEFAULT_SELECTED_SENSOR_IDS_LARGE_SCREEN = ['pressure', 'rain', 'OUT1_temp', 'OUT1_humid']
DEFAULT_SELECTED_SENSOR_IDS_SMALL_SCREEN = ['OUT1_temp', 'rain']

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

AXIS_OFFSET_IN_PX = 80

# represents the lowest possible relative size for the given breakpoint (except for XS)
REL_SECONDARY_AXIS_OFFSET = {
    BootstrapBreakpoint.XS.name: 1.5 * AXIS_OFFSET_IN_PX / BREAKPOINT_WIDTH_IN_PX[BootstrapBreakpoint.SM],
    BootstrapBreakpoint.SM.name: AXIS_OFFSET_IN_PX / BREAKPOINT_WIDTH_IN_PX[BootstrapBreakpoint.SM],
    BootstrapBreakpoint.MD.name: AXIS_OFFSET_IN_PX / BREAKPOINT_WIDTH_IN_PX[BootstrapBreakpoint.MD],
    BootstrapBreakpoint.LG.name: AXIS_OFFSET_IN_PX / (8 / 12 * BREAKPOINT_WIDTH_IN_PX[BootstrapBreakpoint.LG]),
    BootstrapBreakpoint.XL.name: AXIS_OFFSET_IN_PX / (8 / 12 * BREAKPOINT_WIDTH_IN_PX[BootstrapBreakpoint.XL]),
    BootstrapBreakpoint.XXL.name: AXIS_OFFSET_IN_PX / (8 / 12 * BREAKPOINT_WIDTH_IN_PX[BootstrapBreakpoint.XXL]),
}
