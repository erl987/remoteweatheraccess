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
import os
import datetime


def get_bucket_id():
    bucket_address = os.environ['BUCKET']
    bucket_id = bucket_address.replace('gs://', '')
    bucket_id = bucket_id.replace('/', '')

    return bucket_id


def get_default_month():
    if datetime.date.today().day == 1:
        last_day_of_prev_month = datetime.date.today() - datetime.timedelta(days=1)
        return last_day_of_prev_month.month, last_day_of_prev_month.year
    else:
        return datetime.date.today().month, datetime.date.today().year
