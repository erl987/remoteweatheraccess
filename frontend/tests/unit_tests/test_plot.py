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

from frontend.frontend_src.plot import get_scalings, determine_plot_axis_setup

SOME_MIN_MAX_VALUES_OF_SENSORS = {
    'pressure': {
        'min': 980.5,
        'max': 1030.5
    },
    'temperature': {
        'min': -15.3,
        'max': 20.5
    },
    'humidity': {
        'min': 29.4,
        'max': 79.5
    },
    'rain': {
        'min': 0.0,
        'max': 50.5
    },
    'uv': {
        'min': 3.0,
        'max': 5.6
    }
}


def test_get_scalings():
    num_ticks, min_max_values_for_axis = get_scalings(SOME_MIN_MAX_VALUES_OF_SENSORS)
    assert num_ticks == 12
    assert min_max_values_for_axis == {
        'pressure': {
            'min': 980.0,
            'max': 1035.0
        },
        'temperature': {
            'min': -20.0,
            'max': 35.0
        },
        'humidity': {
            'min': 0,
            'max': 100
        },
        'rain': {
            'min': 0,
            'max': 110.0
        },
        'uv': {
            'min': 3.0,
            'max': 5.6}
    }


def test_get_scalings_with_max_num_ticks():
    min_max_values_of_very_large_size = dict(SOME_MIN_MAX_VALUES_OF_SENSORS)
    min_max_values_of_very_large_size['rain']['max'] = 2000
    num_ticks, _ = get_scalings(min_max_values_of_very_large_size)

    assert num_ticks == 15  # the maximum value


def test_get_scaling_with_only_regular_sensors():
    min_max_values_of_sensors = {
        'uv': {
            'min': 3.0,
            'max': 5.6}
    }

    num_ticks, min_max_values_for_axis = get_scalings(min_max_values_of_sensors)
    assert num_ticks == 5
    assert min_max_values_for_axis == min_max_values_of_sensors


def test_determine_plot_axis_setup():
    sensors = ['pressure', 'uv']
    stations = ['TES']
    data = {'TES': {
        'pressure': [1013.5, 1014.9, 1020.9],
        'uv': [9.8, 8.4, 9.3]
    }}
    left_main_axis_pos, right_main_axis_pos, min_max_limits, num_ticks = \
        determine_plot_axis_setup(stations, data, sensors)
    assert left_main_axis_pos == 0.1
    assert right_main_axis_pos == 0.9
    assert min_max_limits == {'pressure': {'min': 1010.0, 'max': 1025.0}, 'uv': {'min': 8.4, 'max': 9.8}}
    assert num_ticks == 4


def test_determinate_plot_axis_setup_when_empty():
    assert determine_plot_axis_setup([], {}, []) == (float('inf'), float('inf'), None, 0)


def test_determinate_plot_axis_setup_when_empty_data():
    sensors = ['pressure']
    stations = ['TES']
    data = {'TES': {'pressure': []}}
    left_main_axis_pos, right_main_axis_pos, min_max_limits, num_ticks = \
        determine_plot_axis_setup(stations, data, sensors)
    assert left_main_axis_pos == 0.1
    assert right_main_axis_pos == 1.0
    assert min_max_limits is None
    assert num_ticks == 0
