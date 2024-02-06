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

import uvicorn
from fastapi import FastAPI, HTTPException
from google.api_core import exceptions
from google.cloud import error_reporting
from google.cloud.logging_v2 import Client
from requests import HTTPError

from export_src.backend_requests import get_sensor_metadata, get_station_metadata_for, get_weather_data_for
from export_src.csv_file import create_pc_weatherstation_compatible_file
from export_src.google_cloud_storage import upload_file
from export_src.utils import get_default_month

app = FastAPI()
logging.basicConfig(level=logging.DEBUG)
is_on_gcp = 'RUNNING_ON_GCP' in os.environ and os.environ['RUNNING_ON_GCP'].lower() == 'true'

if is_on_gcp:
    log_client = Client()
    log_client.setup_logging()

    error_reporting_client = error_reporting.Client()

logger = logging.getLogger()

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

        raise AssertionError("A dummy exception")

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
        if is_on_gcp and e.status_code >= 500:
            error_reporting_client.report_exception()
        raise
    except Exception:
        logger.error(f'Internal server error: {traceback.format_exc()}')
        if is_on_gcp:
            error_reporting_client.report_exception()
        raise HTTPException(status_code=500, detail='Internal server error')


# will only be executed if running directly with Python
if __name__ == '__main__':
    uvicorn.run(app='export_app:app', host='0.0.0.0', port=8000, log_level='info')
