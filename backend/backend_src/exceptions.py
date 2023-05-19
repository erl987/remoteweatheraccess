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

class APIError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None, location=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
        self.location = location

    def to_dict(self, hide_details=True):
        if hide_details and 500 <= self.status_code < 600:
            rv = {'error': '500 INTERNAL SERVER ERROR'}
        else:
            rv = dict(self.payload or ())
            rv['error'] = self.message

        return rv

    def __str__(self):
        return self.message


def formatted_exception_str(e):
    error_type = type(e).__name__
    error_message_list = []
    for item in e.args:
        error_message_list.append(str(item))
    error_message = '. '.join(error_message_list)
    if not error_message:
        error_message = str(e)
        if not error_message:
            return error_type
    return error_type + ': ' + error_message


def raise_api_error(e, status_code):
    if isinstance(e, APIError):
        raise e
    else:
        raise APIError(formatted_exception_str(e), status_code=status_code)
