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
import logging
import os
import signal
import sys
import threading
import time
from argparse import ArgumentParser

import schedule
import yaml
from cerberus import Validator

from client_src.station_interface import WeatherStationProxy

# default settings than can be overwritten by command line arguments
DEFAULT_CONFIG_FILE_PATH = r'./default_client_config.yaml'
DEFAULT_DATA_DIR_PATH = r'../test_data/'
DEFAULT_WEATHER_DATA_READER_PATH = r'../client_helpers/te923con_mock.py'  # path to `te923con` executable in production

CONFIG_FILE_SCHEMA = {
    'station_id': {'type': 'string'},
    'backend_url': {'type': 'string'},
    'backend_port': {'type': 'integer'},
    'use_ssl': {'type': 'boolean'},
    'user_name': {'type': 'string'},
    'relogin_time_in_sec': {'type': 'float'},
    'data_reading': {
        'type': 'dict',
        'schema': {
            'minute_of_first_read_within_an_hour': {'type': 'integer'},
            'read_period_in_minutes': {'type': 'integer'}
        }
    },
    'ignored_data_fields': {
        'type': 'list',
        'schema': {'type': 'string'}
    },
    'sleep_period_in_sec': {'type': 'float'},
    'timeouts_in_min': {
        'type': 'dict',
        'schema': {
            'all_datasets_read': {'type': 'integer'},
            'latest_dataset_read': {'type': 'integer'}
        }
    },
    'logging': {
        'type': 'dict',
        'schema': {
            'do_log_timestamps': {'type': 'boolean'},
            'minimal_log_level': {'type': 'string'}
        }
    }
}


class Runner(object):
    def __init__(self, run_function):
        self.do_stop_program = threading.Event()
        self._run_function = run_function

    def run(self):
        if sys.platform.startswith('win32'):
            self._run_on_windows()
        else:
            self._run_on_linux()

    def _handler_stop_signals(self, _, __):
        """Handles termination events, not used under Windows"""
        logging.debug('Stopping weather station client')
        self.do_stop_program.set()

    def _run_on_linux(self):
        """Stalls the main thread until the program is finished"""
        signal.signal(signal.SIGINT, self._handler_stop_signals)
        signal.signal(signal.SIGTERM, self._handler_stop_signals)

        self._run_function()

    def _run_on_windows(self):
        """Stalls the main thread until the program is finished"""
        # wait for Ctrl + C
        try:
            self._run_function()
        except KeyboardInterrupt:
            pass


class Client(object):
    _REGULAR_STOP = 'REGULAR_STOP'

    def __init__(self, config, data_dir_path, weather_data_reader_path):
        self._config = config
        self._sleep_period_in_sec = config['sleep_period_in_sec']
        self._station_is_free_for_read = threading.Event()
        self._lock = threading.Lock()
        self._weather_station_proxy = WeatherStationProxy(self._config,
                                                          data_dir_path,
                                                          weather_data_reader_path)
        self._runner = Runner(self._perform_run)

    def _read_and_send_data_from_station(self):
        with self._lock:
            if not self._station_is_free_for_read.is_set():
                logging.debug('A previous weather station read is not yet finalized, skipping the reading this time')
                return

            self._station_is_free_for_read.clear()

        try:
            # can take more than 10 minutes if all data needs to be read
            has_read_all_datasets = self._weather_station_proxy.read_and_send_with_automatic_choice()
            if has_read_all_datasets:
                # now the very latest data needs to be read as well - the previous full read took more than one period
                self._weather_station_proxy.read_and_send(do_read_all_datasets=False)
        except Exception as e:
            logging.error('Read or send of data failed: {}'.format(e))
        finally:
            self._station_is_free_for_read.set()

    @staticmethod
    def _run_threaded(job_func):
        job_thread = threading.Thread(target=job_func)
        job_thread.start()

    def run(self):
        self._runner.run()

    @staticmethod
    def _determine_read_time_points_in_hour(minute_of_first_read_within_an_hour, read_period_in_minutes):
        time_points_in_hour = []
        minute_of_hour = minute_of_first_read_within_an_hour
        while minute_of_hour < 60:
            time_points_in_hour.append(':{:02d}'.format(minute_of_hour))
            minute_of_hour += read_period_in_minutes

        return time_points_in_hour

    def _perform_run(self):
        self._station_is_free_for_read.set()

        time_points_in_hour = self._determine_read_time_points_in_hour(
            self._config['data_reading']['minute_of_first_read_within_an_hour'],
            self._config['data_reading']['read_period_in_minutes']
        )

        for time_point in time_points_in_hour:
            schedule.every().hour.at(time_point).do(self._run_threaded, self._read_and_send_data_from_station)

        logging.info('Weather station client has started successfully (version: {})'
                     .format(os.getenv('GIT_COMMIT', 'unknown')))
        while True:
            if self._runner.do_stop_program.is_set():
                break

            schedule.run_pending()
            time.sleep(self._sleep_period_in_sec)

        logging.info('Weather station client has stopped successfully')


def get_command_line_arguments():
    parser = ArgumentParser(description='Weather station client reading the data regularly and sending it to a'
                                        'backend server.')
    parser.add_argument('--config-file', '-c', default=DEFAULT_CONFIG_FILE_PATH,
                        help='The path to the YAML configuration file')
    parser.add_argument('--data-dir', '-d', default=DEFAULT_DATA_DIR_PATH,
                        help='The directory for data written by the program')
    parser.add_argument('--weather-data-reader-file', '-r', default=DEFAULT_WEATHER_DATA_READER_PATH,
                        help='The path to the executable te923con')

    args = parser.parse_args()
    return args.config_file, args.data_dir, args.weather_data_reader_file


def configure_logging(config):
    if config['logging']['do_log_timestamps']:
        format_str = '%(asctime)s %(levelname)-8s %(message)s'
    else:
        format_str = '%(levelname)-8s %(message)s'

    minimal_log_level = logging.getLevelName(config['logging']['minimal_log_level'])
    if not isinstance(minimal_log_level, int):
        raise SyntaxError('Unknown minimal log level: {}'.format(minimal_log_level))

    logging.basicConfig(level=minimal_log_level,
                        format=format_str,
                        datefmt='%d.%m.%Y %H:%M:%S')


def load_config_file(config_file_path):
    config_file_is_not_present = False

    if not os.path.isfile(config_file_path):
        config_file_path = DEFAULT_CONFIG_FILE_PATH
        config_file_is_not_present = True

    with open(config_file_path) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    validator = Validator(CONFIG_FILE_SCHEMA, require_all=True)
    validator.validate(config)

    if validator.errors:
        raise SyntaxError('Syntax of config file \'{}\' is invalid: {}'.format(config_file_path, validator.errors))

    return config, config_file_is_not_present, config_file_path


def main():
    try:
        config_file_path, data_dir_path, weather_data_reader_path = get_command_line_arguments()
        config, config_file_is_not_present, actual_config_file_path = load_config_file(config_file_path)
        configure_logging(config)
        logging.info('Loading the config file \'{}\''.format(actual_config_file_path))
        if config_file_is_not_present:
            logging.warning('Config file \'{}\' is not present, using the default config file instead'
                            .format(config_file_path))
    except Exception as e:
        print('Fatal error while loading configuration: {}: {}'.format(type(e).__name__, str(e)))
        sys.exit(-1)

    try:
        logging.debug('Starting weather station client')
        client = Client(config, data_dir_path, weather_data_reader_path)
        client.run()
    except Exception as e:
        print('Fatal error: {}: {}'.format(type(e).__name__, e))
        sys.exit(-2)


if __name__ == '__main__':
    main()
