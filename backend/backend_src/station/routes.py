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

from flask import jsonify, request, current_app, Blueprint, Response

from .schemas import weather_station_schema, many_weather_stations_schema
from ..exceptions import APIError
from ..extensions import db
from ..models import WeatherStation
from ..utils import json_with_rollback_and_raise_exception, access_level_required, Role, \
    with_rollback_and_raise_exception, convert_to_int

station_blueprint = Blueprint('station', __name__, url_prefix='/api/v1/station')


@station_blueprint.route('', methods=['POST'])
@access_level_required(Role.ADMIN)
@json_with_rollback_and_raise_exception
def add_station():
    new_station = weather_station_schema.load(request.json)

    existing_station = WeatherStation.query.filter_by(station_id=new_station.station_id).one_or_none()
    if not existing_station:
        db.session.add(new_station)
        db.session.commit()
        response = jsonify(weather_station_schema.dump(new_station))
        current_app.logger.info('Added new station \'{}\' to the database'.format(new_station.station_id))
        response.status_code = HTTPStatus.CREATED
    else:
        raise APIError('Station \'{}\' already in the database'.format(new_station.station_id),
                       status_code=HTTPStatus.CONFLICT, location='/api/v1/station/{}'.format(existing_station.id))

    response.headers['location'] = '/api/v1/station/{}'.format(new_station.id)

    return response


@station_blueprint.route('', methods=['GET'])
@access_level_required(Role.GUEST)
@with_rollback_and_raise_exception
def get_all_stations():
    all_stations = WeatherStation.query.all()
    response = jsonify(many_weather_stations_schema.dump(all_stations))
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Provided details for all {} stations'.format(len(all_stations)))

    return response


@station_blueprint.route('/<numeric_station_id>', methods=['GET'])
@access_level_required(Role.GUEST)
@with_rollback_and_raise_exception
def get_station_details(numeric_station_id):
    station = WeatherStation.query.get(convert_to_int(numeric_station_id))
    if not station:
        raise APIError('No station with id \'{}\''.format(numeric_station_id), status_code=HTTPStatus.BAD_REQUEST)

    response = jsonify(weather_station_schema.dump(station))
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Provided details for station \'{}\''.format(station.station_id))

    return response


@station_blueprint.route('/<numeric_station_id>', methods=['PUT'])
@access_level_required(Role.ADMIN)
@with_rollback_and_raise_exception
def update_station(numeric_station_id):
    updated_station = weather_station_schema.load(request.json)

    existing_station = WeatherStation.query.get(convert_to_int(numeric_station_id))
    if not existing_station:
        raise APIError('No station with id \'{}\''.format(numeric_station_id), status_code=HTTPStatus.NOT_FOUND)

    if updated_station.station_id != existing_station.station_id:
        raise APIError('The station \'{}\' stored for id \'{}\' does not match the name \'{}\' of the submitted '
                       'station'.format(existing_station.station_id, numeric_station_id, updated_station.station_id),
                       status_code=HTTPStatus.CONFLICT,
                       location='/api/v1/station/{}'.format(existing_station.id))

    existing_station.device = updated_station.device
    existing_station.location = updated_station.location
    existing_station.latitude = updated_station.latitude
    existing_station.longitude = updated_station.longitude
    existing_station.height = updated_station.height
    existing_station.rain_calib_factor = updated_station.rain_calib_factor
    db.session.add(existing_station)
    db.session.commit()
    current_app.logger.info('Updated station \'{}\' in the database'.format(existing_station.station_id))

    response = Response('')
    response.status_code = HTTPStatus.NO_CONTENT
    response.headers['location'] = '/api/v1/station/{}'.format(existing_station.id)

    return response


@station_blueprint.route('/<numeric_station_id>', methods=['DELETE'])
@access_level_required(Role.ADMIN)
@with_rollback_and_raise_exception
def remove_station(numeric_station_id):
    existing_station = WeatherStation.query.get(convert_to_int(numeric_station_id))
    if not existing_station:
        current_app.logger.info('No station with id \'{}\' '.format(numeric_station_id))
        return '', HTTPStatus.NO_CONTENT

    db.session.delete(existing_station)
    db.session.commit()
    current_app.logger.info('Deleted station \'{}\' from the database'.format(existing_station.station_id))

    return '', HTTPStatus.NO_CONTENT
