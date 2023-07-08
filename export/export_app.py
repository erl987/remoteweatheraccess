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
import traceback
from logging.config import dictConfig

import uvicorn
from fastapi import FastAPI, HTTPException
from google.api_core import exceptions
from pydantic import BaseModel
from requests import HTTPError

from export_src.backend_requests import get_sensor_metadata, get_station_metadata_for, get_weather_data_for
from export_src.csv_file import create_pc_weatherstation_compatible_file
from export_src.google_cloud_storage import upload_file
from export_src.utils import get_default_month


class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    LOGGER_NAME: str = 'exporter'
    LOG_FORMAT: str = '%(levelprefix)s %(message)s'
    LOG_LEVEL: str = 'DEBUG'

    # Logging config
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict = {
        'default': {
            '()': 'uvicorn.logging.DefaultFormatter',
            'fmt': LOG_FORMAT,
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    }
    handlers: dict = {
        'default': {
            'formatter': 'default',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
        },
    }
    loggers: dict = {
        'exporter': {'handlers': ['default'], 'level': LOG_LEVEL},
    }


app = FastAPI()
dictConfig(LogConfig().model_dump())
logger = logging.getLogger('exporter')

backend_url = os.environ['BACKEND_URL']
port = os.environ['BACKEND_PORT']
csv_file_dir = os.getenv('CSV_FILE_DIR', 'tests/test_data')


@app.post('/upload')
async def create_and_upload_csv_file(station_id: str = None, month: int = None, year: int = None):
    try:
        if month is not None:
            if month < 1 or month > 12:
                raise HTTPException(status_code=422, detail='Month is out of range 1 - 12')

        if (not month and year) or (not year and month):
            raise HTTPException(status_code=422, detail='Both month and year need to be specified or none of them')

        if not month and not year:
            month, year = get_default_month()
            logger.debug('No month specified in the request, using the default: {}/{}'.format(month, year))

        try:
            sensor_metadata = get_sensor_metadata(backend_url, port)
            all_station_metadata = get_station_metadata_for(backend_url, port, station_id)
        except ValueError:
            raise HTTPException(status_code=422, detail=f'Station {station_id} is not available')
        except HTTPError:
            raise HTTPException(status_code=503, detail='Backend API is not available')

        for station_metadata in all_station_metadata:
            curr_station_id = station_metadata['station_id']

            try:
                month_data = get_weather_data_for(month, year, curr_station_id, backend_url, port)
            except HTTPError:
                raise HTTPException(status_code=503, detail='Backend API is not available')

            csv_file_path = create_pc_weatherstation_compatible_file(month_data, curr_station_id, month, year,
                                                                     sensor_metadata, station_metadata, csv_file_dir)

            try:
                upload_file(csv_file_path, curr_station_id)
            except (exceptions.TooManyRequests, exceptions.InternalServerError, exceptions.BadGateway,
                    exceptions.ServiceUnavailable):
                raise HTTPException(status_code=503, detail='Storage API is not available')

        return {'result': 'ok'}
    except HTTPException as e:
        logger.error(f'Status code: {e.status_code}, error: {e.detail}')
        raise
    except Exception:
        logger.error(f'Internal server error: {traceback.format_exc()}')
        raise HTTPException(status_code=500, detail='Internal server error')


# will only be executed if running directly with Python
if __name__ == '__main__':
    uvicorn.run(app='export_app:app', host='0.0.0.0', port=8000, log_level='info')
