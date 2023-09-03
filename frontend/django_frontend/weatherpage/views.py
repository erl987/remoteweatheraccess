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

from datetime import datetime, timezone, timedelta
from os import environ

from django.shortcuts import render
from django.views.generic import TemplateView

# noinspection PyUnresolvedReferences
from . import dash_download_page_app
# noinspection PyUnresolvedReferences
from . import dash_weatherpage_app
from .dash_weatherpage.backend_proxy import CachedBackendProxy
from .dash_weatherpage.dash_settings import BACKEND_URL, BACKEND_PORT, BACKEND_DO_USE_HTTPS


def main(request):
    return render(request, 'weatherpage/weatherdata.html', context={'BRAND_NAME': environ.get('BRAND_NAME')})


# noinspection PyUnusedLocal
def main_for_station(request, station_id):
    return render(request, 'weatherpage/weatherdata.html', context={'BRAND_NAME': environ.get('BRAND_NAME')})


def download(request):
    return render(request, 'weatherpage/download.html', context={'BRAND_NAME': environ.get('BRAND_NAME')})


def impress(request):
    return render(request, 'weatherpage/impress.html', context={'BRAND_NAME': environ.get('BRAND_NAME')})


def policy(request):
    return render(request, 'weatherpage/policy.html', context={'BRAND_NAME': environ.get('BRAND_NAME')})


class LatestDataView(TemplateView):
    template_name = 'weatherpage/latest_data.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=3)

        station_id = 'TES'  # TODO: to be determined by user

        backend_proxy = CachedBackendProxy(BACKEND_URL, BACKEND_PORT, BACKEND_DO_USE_HTTPS)
        latest_data = backend_proxy.data([station_id], [], start_time, end_time)
        available_sensors = backend_proxy.available_sensors()
        available_stations = backend_proxy.available_stations()

        sensor_data = []
        for sensor_id, values in latest_data[station_id].items():
            if sensor_id == 'timepoint':
                continue

            if sensor_id == 'temperature_humidity':
                for temp_humid_sensor_id, subsensors in values.items():
                    for subsensor_id, sub_values in subsensors.items():
                        if subsensor_id == 'temperature':
                            short_subsensor_id = 'temp'
                        elif subsensor_id == 'humidity':
                            short_subsensor_id = 'humid'
                        else:
                            short_subsensor_id = subsensor_id
                        this_sensor_id = f'{temp_humid_sensor_id}_{short_subsensor_id}'
                        human_readable_name = available_sensors[1][this_sensor_id]['description']
                        unit = available_sensors[1][this_sensor_id]['unit']
                        sensor_data.append({'description': human_readable_name, 'unit': unit, 'value': sub_values[-1]})
            else:
                human_readable_name = available_sensors[1][sensor_id]['description']
                unit = available_sensors[1][sensor_id]['unit']
                sensor_data.append({'description': human_readable_name, 'unit': unit, 'value': values[-1]})

        context['time_point'] = latest_data[station_id]['timepoint'][-1]
        context['sensor_data'] = sensor_data
        context['stations'] = available_stations[0]

        return context
