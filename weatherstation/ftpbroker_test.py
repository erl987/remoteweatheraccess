import time
from weathernetwork.server.ftpbroker import FTPServerSideProxy
from weathernetwork.server.sqldatabaseservice import SQLDatabaseServiceFactory

if __name__ == "__main__":
    db_file_name = "data/weather.db"

    sql_database_service_factory = SQLDatabaseServiceFactory(db_file_name)
    proxy = FTPServerSideProxy(sql_database_service_factory)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass