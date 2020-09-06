from frontend.src.plot import get_scalings

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
    assert num_ticks ==5
    assert min_max_values_for_axis == min_max_values_of_sensors
