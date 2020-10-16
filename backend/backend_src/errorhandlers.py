#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2020 Ralf Rettig (info@personalfme.de)
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

from http import HTTPStatus

from flask import jsonify, current_app

from .exceptions import APIError


def handle_invalid_usage(error):
    response = jsonify(error.to_dict(hide_details=True))
    response.status_code = error.status_code
    if error.location:
        response.headers['location'] = error.location
    current_app.logger.error('HTTP-Statuscode {}: {}'.format(error.status_code, error.to_dict(hide_details=False)))

    return response


def unauthorized_response(_):
    error = APIError('Missing Authorization header', status_code=HTTPStatus.UNAUTHORIZED)
    response = jsonify(error.to_dict(hide_details=False))
    response.status_code = error.status_code
    current_app.logger.error('HTTP-Statuscode {}: {}'.format(error.status_code, error.to_dict(hide_details=False)))
    return response
