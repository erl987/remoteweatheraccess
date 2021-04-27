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
import logging
import signal
import sys
import threading
import time

import schedule
import yaml

from client_src.station_interface import WeatherStationProxy

CONFIG_FILE_PATH = r'./client_config/client_config.yaml'


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
    _REGULAR_STOP = "REGULAR_STOP"
    _READ_PERIOD_IN_MINUTES = 10

    def __init__(self):
        with open(CONFIG_FILE_PATH) as file:
            self._config = yaml.load(file, Loader=yaml.FullLoader)

        self._station_is_free_for_read = threading.Event()
        self._weather_station_proxy = WeatherStationProxy(self._config, Client._READ_PERIOD_IN_MINUTES)
        self._runner = Runner(self._perform_run)

    def _read_and_send_data_from_station(self):
        self._station_is_free_for_read.wait()
        try:
            self._weather_station_proxy.read_and_send()  # can take more than 10 minutes if all data needs to be read
        except Exception as e:
            logging.error('Read or send of data failed: {}'.format(e))
        finally:
            self._station_is_free_for_read.set()

    @staticmethod
    def _run_threaded(job_func):
        job_thread = threading.Thread(target=job_func)
        job_thread.start()

    def run(self):
        logging.basicConfig(level=logging.INFO)
        self._runner.run()

    def _perform_run(self):
        self._station_is_free_for_read.set()

        for time_point in self._config['read_time_points_in_hour']:
            schedule.every().hour.at(time_point).do(self._run_threaded, self._read_and_send_data_from_station)

        while True:
            if self._runner.do_stop_program.is_set():
                break

            schedule.run_pending()
            time.sleep(0.25)


if __name__ == '__main__':
    runner = Client()
    runner.run()
