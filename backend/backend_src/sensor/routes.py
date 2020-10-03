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

from flask import Blueprint, jsonify, current_app

from .models import Sensor
from ..exceptions import APIError
from ..extensions import db
from ..utils import with_rollback_and_raise_exception, access_level_required, Role

sensor_blueprint = Blueprint('sensor', __name__, url_prefix='/api/v1/sensor')


@sensor_blueprint.route('', methods=['GET'])
@access_level_required(Role.GUEST)
@with_rollback_and_raise_exception
def get_all_sensors():
    sensor_data = db.session.query(Sensor).all()

    current_app.logger.info('Provided details for all {} sensors'.format(len(sensor_data)))
    response = jsonify(sensor_data)
    response.status_code = HTTPStatus.OK
    return response


@sensor_blueprint.route('/<sensor_id>', methods=['GET'])
@access_level_required(Role.GUEST)
@with_rollback_and_raise_exception
def get_a_sensor(sensor_id):
    sensor_id = sensor_id.lower()
    sensor_data = (db.session
                   .query(Sensor)
                   .filter(Sensor.sensor_id == sensor_id)
                   .one_or_none())

    if not sensor_data:
        raise APIError('No sensor with such id', status_code=HTTPStatus.BAD_REQUEST)
    else:
        current_app.logger.info('Provided details for sensor \'{}\''.format(sensor_id))
        response = jsonify(sensor_data)
        response.status_code = HTTPStatus.OK
        return response
