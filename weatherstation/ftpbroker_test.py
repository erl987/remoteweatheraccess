import sys
import time
import logging
from watchdog.observers import Observer
from weathernetwork.server.ftpbroker import FTPServerSideProxy
from weathernetwork.server.iweatherpersistenceservice import IWeatherPersistenceService
from weathernetwork.server.weatherpersistenceservice import WeatherPersistenceService
from weathernetwork.server.storageprocess import StorageProcess
from weathernetwork.server.mockbroker.mockserversideproxy import MockServerSideProxy # TODO: temp

class MockPersistenceService(IWeatherPersistenceService):
    """Mock class for a service storing weather data in a database"""

    def add_data(self, message):
        print(message)


if __name__ == "__main__":
    db_file_name = "data/weather.db"

    proxy = FTPServerSideProxy()
    storage_process = StorageProcess()
    with WeatherPersistenceService(proxy, storage_process, db_file_name) as persistenceService:
        try:
            while True:
                persistenceService.wait_for_next_data()
                persistenceService.check_for_exceptions_in_processes()
        except KeyboardInterrupt:
            pass
