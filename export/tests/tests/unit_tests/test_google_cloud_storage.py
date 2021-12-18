#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2021 Ralf Rettig (info@personalfme.de)
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

import os
from unittest.mock import patch

from export_src.google_cloud_storage import upload_file
from tests.tests.utils import set_mocks_up


@patch.dict(os.environ, {'BUCKET_ID': 'a-bucket-id-###'})
@patch('os.path.getsize')
@patch('export_src.utils.get_bucket_id')
@patch('google.cloud.storage.Client')
def test_upload_file(storage_client, get_bucket_id, os_get_size):
    file_name = 'some_file.csv'
    local_file_path = os.path.join('some_path', file_name)
    storage_folder = 'TES'

    bucket_mock, object_blob_mock = set_mocks_up(get_bucket_id, os_get_size, storage_client)

    upload_file(local_file_path, storage_folder)

    assert bucket_mock.blob.call_count == 1
    assert bucket_mock.blob.call_args[0][0] == os.path.join(storage_folder, file_name)
    assert object_blob_mock.upload_from_filename.call_count == 1
    assert object_blob_mock.upload_from_filename.call_args[1]['filename'] == local_file_path


@patch.dict(os.environ, {'BUCKET_ID': 'a-bucket-id-###'})
@patch('os.path.getsize')
@patch('export_src.utils.get_bucket_id')
@patch('google.cloud.storage.Client')
def test_upload_file_when_no_local_file(storage_client, get_bucket_id, os_get_size):
    storage_folder = 'TES'

    bucket_mock, object_blob_mock = set_mocks_up(get_bucket_id, os_get_size, storage_client)

    upload_file(None, storage_folder)

    assert bucket_mock.blob.call_count == 0
    assert object_blob_mock.upload_from_filename.call_count == 0
