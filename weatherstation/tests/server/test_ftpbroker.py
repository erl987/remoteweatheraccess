# RemoteWeatherAccess - Weather network connecting to remote stations
# Copyright(C) 2013-2016 Ralf Rettig (info@personalfme.de)
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
import threading
import time
import unittest
from functools import partial
from multiprocessing import Process, Queue

from watchdog.events import FileSystemEvent

from weathernetwork.server.ftpbroker import FileSystemObserver


def data_directory():
    return "./data/unittests/ftpbroker"


def not_existing_data_directory():
    return "./data/unittests/notexisting"


def a_file_path():
    return data_directory() + os.sep + "test.zip"


def create_a_data_file():
    with open(a_file_path(), "w") as file:
        file.write("This is a dummy file that has not a valid format.")


def _exception_handler(exception, queue):
    queue.put(exception)


class TestFileSystemObserver(unittest.TestCase):
    def setUp(self):
        self._exception = None
        self._received_file_queue = Queue()

        if os.path.isdir(data_directory()):
            shutil.rmtree(data_directory(), ignore_errors=True)
        os.makedirs(data_directory(), exist_ok=True)  # creates the test directory if required

    def tearDown(self):
        pass

    def test_on_modified(self):
        # given:
        file_system_observer = FileSystemObserver(data_directory())
        file_system_observer.set_received_file_queue(self._received_file_queue)
        file_system_observer._processed_files_lock = threading.Lock()
        modified_event = FileSystemEvent(a_file_path())

        # when:
        file_system_observer.on_modified(modified_event)
        time.sleep(0.3)

        # then:
        self.assertFalse(self._received_file_queue.empty())
        if not self._received_file_queue.empty():
            got_filepath = self._received_file_queue.get()
            self.assertEqual(got_filepath, a_file_path())

    def test_process(self):
        # given:
        filesystem_observer = FileSystemObserver(data_directory())
        filesystem_observer_process = Process(
            target=filesystem_observer.process, args=(self._received_file_queue, _exception_handler)
        )
        filesystem_observer_process.start()
        time.sleep(1.0)  # significant waiting time is required to start the file watching reliably

        # when:
        create_a_data_file()
        got_filepath = self._received_file_queue.get()
        filesystem_observer.stop()

        # then:
        self.assertEqual(got_filepath, a_file_path())

    def test_process_exception_transfer(self):
        # given:
        exception_queue = Queue()
        filesystem_observer = FileSystemObserver(not_existing_data_directory())

        # when:
        filesystem_observer_process = Process(
            target=filesystem_observer.process, args=(self._received_file_queue,
                                                      partial(_exception_handler, queue=exception_queue))
        )
        filesystem_observer_process.start()
        got_exception = exception_queue.get()

        # then:
        self.assertRaises(IOError, got_exception.re_raise)

    def test_feed_modified_file(self):
        # given:
        file_system_observer = FileSystemObserver(data_directory())
        file_system_observer.set_received_file_queue(self._received_file_queue)

        # when:
        file_system_observer.feed_modified_file(a_file_path())
        time.sleep(0.3)

        # then:
        self.assertFalse(self._received_file_queue.empty())
        if not self._received_file_queue.empty():
            got_filepath = self._received_file_queue.get()
            self.assertEqual(got_filepath, a_file_path())


if __name__ == '__main__':
    unittest.main()
