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

from http import HTTPStatus

from flask import Blueprint, jsonify, current_app

from ..exceptions import APIError
from ..extensions import db
from ..models import TempHumiditySensor
from ..utils import with_rollback_and_raise_exception, access_level_required, Role

temp_humidity_sensor_blueprint = Blueprint('temp_humidity_sensor', __name__, url_prefix='/api/v1/temp-humidity-sensor')


@temp_humidity_sensor_blueprint.route('', methods=['GET'])
@access_level_required(Role.GUEST)
@with_rollback_and_raise_exception
def get_all_temp_humidity_sensors():
    sensor_data = (db.session
                   .query(TempHumiditySensor)
                   .with_entities(TempHumiditySensor.sensor_id, TempHumiditySensor.description)
                   .all())

    current_app.logger.info('Provided details of all {} temperature-humidity sensors'.format(len(sensor_data)))
    response = jsonify(_sensor_data_to_json(sensor_data))
    response.status_code = HTTPStatus.OK
    return response


@temp_humidity_sensor_blueprint.route('/<sensor_id>', methods=['GET'])
@access_level_required(Role.GUEST)
@with_rollback_and_raise_exception
def get_a_temp_humidity_sensor(sensor_id):
    sensor_id = sensor_id.upper()
    sensor_data = (db.session
                   .query(TempHumiditySensor)
                   .with_entities(TempHumiditySensor.sensor_id, TempHumiditySensor.description)
                   .filter(TempHumiditySensor.sensor_id == sensor_id)
                   .one_or_none())

    if not sensor_data:
        raise APIError('No such temperature-humidity sensor', status_code=HTTPStatus.BAD_REQUEST)
    else:
        current_app.logger.info('Provided details for temperature-humidity sensor \'{}\''.format(sensor_id))

        response = jsonify(_sensor_data_to_json([sensor_data])[0])
        response.status_code = HTTPStatus.OK
        return response


def _sensor_data_to_json(sensor_data):
    sensor_data_json = []
    for row in sensor_data:
        sensor_id, description = row
        sensor_data_json.append({'sensor_id': sensor_id, 'description': description})

    return sensor_data_json
