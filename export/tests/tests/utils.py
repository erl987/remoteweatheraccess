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

from unittest.mock import MagicMock

import pandas as pd
from google.cloud import storage


def set_mocks_up(get_bucket_id, os_get_size, storage_client):
    object_blob_mock = MagicMock(autospec=storage.Blob)

    bucket_mock = MagicMock(autospec=storage.Bucket)
    bucket_mock.blob.return_value = object_blob_mock

    storage_client_mock = MagicMock(autospec=storage.Client)
    storage_client_mock.bucket.return_value = bucket_mock

    get_bucket_id.return_value = 'a-bucket-id-12345'

    storage_client.return_value = storage_client_mock
    os_get_size.return_value = 134895324

    return bucket_mock, object_blob_mock


def csv_files_do_match(expected_csv_file_path, reference_csv_file_path):
    read_data = pd.read_csv(expected_csv_file_path)
    reference_data = pd.read_csv(reference_csv_file_path)

    if len(reference_data.compare(read_data)) > 0:
        print(reference_data.compare(read_data))

    return len(reference_data.compare(read_data)) == 0
