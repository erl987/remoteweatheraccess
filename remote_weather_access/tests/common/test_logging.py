# RemoteWeatherAccess - Weather network connecting to remote stations
# Copyright(C) 2013-2017 Ralf Rettig (info@personalfme.de)
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.If not, see <http://www.gnu.org/licenses/>

import os
import shutil
import unittest
from multiprocessing import Process

from remote_weather_access.common.exceptions import RunInNotAllowedProcessError
from remote_weather_access.common.logging import MultiProcessLogger, MultiProcessLoggerProxy
from remote_weather_access.server.config import LogConfigSection


def log_file_name():
    return "./tests/workingDir/logging/test_log.txt"


def message_text():
    return "Test message"


def multiprocess_message_text():
    return "Multiprocess test message"


def _logger_process(logging_connection):
    logger_proxy = MultiProcessLoggerProxy(logging_connection)
    logger_proxy.log(MultiProcessLogger.ERROR, multiprocess_message_text())


def prepare_directory():
    log_dir = os.path.dirname(log_file_name())
    if os.path.isdir(log_dir):
        shutil.rmtree(log_dir, ignore_errors=False)
    os.makedirs(log_dir, exist_ok=True)  # creates the test directory if required


class TestMultiProcessLogger(unittest.TestCase):
    def setUp(self):
        prepare_directory()

    def tearDown(self):
        pass

    def test_log(self):
        # given:
        log_config = LogConfigSection(log_file_name(), 100, 10)

        # when:
        with MultiProcessLogger(True, log_config) as logger:
            logger.log(MultiProcessLogger.ERROR, message_text())

        with open(log_file_name(), 'r') as file:
            log_file_content = file.read()

        # then:
        self.assertTrue(message_text() in log_file_content)


class TestMultiProcessProxyLogger(unittest.TestCase):
    def setUp(self):
        prepare_directory()

    def tearDown(self):
        pass

    def test_log_on_same_process(self):
        # given:
        log_config = LogConfigSection(log_file_name(), 100, 10)

        # when:
        with MultiProcessLogger(True, log_config) as logger:
            # then:
            self.assertRaises(RunInNotAllowedProcessError, MultiProcessLoggerProxy, logger.get_connection())

    def test_log(self):
        # given:
        log_config = LogConfigSection(log_file_name(), 100, 10)

        # when:
        with MultiProcessLogger(True, log_config) as logger:
            p = Process(target=_logger_process, args=(logger.get_connection(),))
            p.start()
            p.join()

        with open(log_file_name(), 'r') as file:
            log_file_content = file.read()

        # then:
        self.assertTrue(multiprocess_message_text() in log_file_content)


if __name__ == '__main__':
    unittest.main()
