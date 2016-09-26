from weathernetwork.server.ftpbroker import FTPServerSideProxy
from weathernetwork.server.sqldatabase import SQLDatabaseServiceFactory
from multiprocessing import Queue


def on_message(message):
    """Receives messages that should be logged."""
    print(message.get_message())


if __name__ == "__main__":
    db_file_name = "data/weather.db"
    data_directory = "C:\\Users\\Ralf\\Documents\\test"
    temp_data_directory = "C:\\Users\\Ralf\\Desktop\\temp"
    data_file_extension = ".ZIP"
    delta_time = 10     # time difference between two datasets (in minutes)

    exception_queue = Queue()
    sql_database_service_factory = SQLDatabaseServiceFactory(db_file_name)

    with FTPServerSideProxy(sql_database_service_factory, data_directory, data_file_extension, temp_data_directory, on_message, exception_queue, delta_time) as proxy:
        # stall the main thread until the program is finished
        exception_from_subprocess = []
        try:
            exception_from_subprocess = exception_queue.get()
        except KeyboardInterrupt:
            pass

        if exception_from_subprocess:
            exception_from_subprocess.re_raise()
