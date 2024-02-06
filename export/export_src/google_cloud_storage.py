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
import time

from google.cloud import logging as gcp_logging
from google.cloud import storage

from export_src import utils

logger = logging.getLogger('exporter')


def upload_file(local_file_path, storage_folder):
    if not local_file_path:
        logger.debug('No CSV-file had been generated, skipping the upload')
        return

    service_account_json = os.getenv('GCP_SERVICE_ACCOUNT_JSON', None)
    if service_account_json:
        storage_client = storage.Client.from_service_account_json(service_account_json)
    else:
        storage_client = storage.Client()

    bucket_id = utils.get_bucket_id()
    logger.debug('Uploading "{}" to bucket "{}" ...'.format(local_file_path, bucket_id))

    bucket = storage_client.bucket(bucket_id)
    file_name = os.path.basename(local_file_path)
    object_blob = bucket.blob(os.path.join(storage_folder, file_name))

    start_time = time.time()
    # this will override existing objects (if not prevented by the bucket versioning and lifecycle policies)
    object_blob.upload_from_filename(filename=local_file_path)
    end_time = time.time()

    elapsed_time_in_sec = end_time - start_time
    file_size_in_mb = os.path.getsize(local_file_path) / 1.0e6
    upload_rate_in_mbit_per_sec = 8 * file_size_in_mb / elapsed_time_in_sec
    logger.debug('... done ({:.1f} MB), {:.1f} Mbit/s'.format(file_size_in_mb, upload_rate_in_mbit_per_sec))


def configure_gcp_logging():
    client = gcp_logging.Client()
    client.setup_logging()

    return client
