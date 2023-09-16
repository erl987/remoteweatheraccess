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

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import FormView

# noinspection PyUnresolvedReferences
from . import dash_download_page_app
# noinspection PyUnresolvedReferences
from . import dash_weatherpage_app
from .dash_weatherpage.backend_proxy import CachedBackendProxy
from .dash_weatherpage.dash_settings import BACKEND_URL, BACKEND_PORT, BACKEND_DO_USE_HTTPS
from .forms import LatestDataForm


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


class LatestDataView(FormView):
    template_name = 'weatherpage/latest_data.html'
    form_class = LatestDataForm

    SPECIAL_SENSOR_IDS = ['direction', 'gusts', 'rain_rate', 'speed', 'wind_temperature', 'uv']
    GENERAL_SENSOR_ORDER = ['temperature', 'humidity', 'rain', 'dewpoint']

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=3)

        station_id = self.kwargs.get('station_id', None)

        backend_proxy = CachedBackendProxy(BACKEND_URL, BACKEND_PORT, BACKEND_DO_USE_HTTPS)
        if not station_id:
            station_id = backend_proxy.available_stations()[0][-1]['value']
        latest_data = backend_proxy.data([station_id], [], start_time, end_time)
        available_sensors = backend_proxy.available_sensors()

        if len(latest_data) > 0:
            sensor_data = []
            special_sensor_data = []
            for sensor_id, values in latest_data[station_id].items():
                if sensor_id == 'timepoint':
                    continue

                if sensor_id == 'temperature_humidity':
                    for temp_humid_sensor_id, subsensors in values.items():
                        for subsensor_id, sub_values in subsensors.items():
                            sensor_data.append(
                                self._get_subsensor_data(subsensor_id, temp_humid_sensor_id, sub_values[-1],
                                                         available_sensors))
                else:
                    this_sensor_data = self._get_sensor_data(sensor_id, values[-1], available_sensors)
                    self._replace_sensor_descritions(this_sensor_data)

                    if sensor_id not in LatestDataView.SPECIAL_SENSOR_IDS:
                        sensor_data.append(this_sensor_data)
                    else:
                        special_sensor_data.append(this_sensor_data)

            sensor_data = sorted(sensor_data, key=lambda d: d['description'])

            context['time_point'] = datetime.fromisoformat(latest_data[station_id]['timepoint'][-1])
            context['sensor_data'] = sorted(sensor_data, key=lambda d: d['description'])
            context['special_sensor_data'] = sorted(special_sensor_data, key=lambda d: d['description'])

        return context

    @staticmethod
    def _replace_sensor_descritions(this_sensor_data):
        if this_sensor_data['description'] == 'Regen':
            this_sensor_data['description'] = 'Regen (letzte 24 Stunden)'
        if this_sensor_data['description'] == 'Regenrate':
            this_sensor_data['description'] = 'Regen (letzte 10 Minuten)'
        if this_sensor_data['description'] == 'Windböen':
            this_sensor_data['description'] = 'Böen (letzte 10 Minuten)'
        if this_sensor_data['description'] == 'Windgeschwindigkeit':
            this_sensor_data['description'] = 'Wind (letzte 10 Minuten)'

    @staticmethod
    def _get_subsensor_data(subsensor_id, temp_humid_sensor_id, last_value, available_sensors):
        if subsensor_id == 'temperature':
            short_subsensor_id = 'temp'
        elif subsensor_id == 'humidity':
            short_subsensor_id = 'humid'
        else:
            short_subsensor_id = subsensor_id
        this_sensor_id = f'{temp_humid_sensor_id}_{short_subsensor_id}'
        human_readable_name = available_sensors[1][this_sensor_id]['description']
        unit = available_sensors[1][this_sensor_id]['unit']

        return {'description': human_readable_name, 'value': LatestDataView._get_presented_value(last_value, unit)}

    @staticmethod
    def _get_sensor_data(sensor_id, last_value, available_sensors):
        human_readable_name = available_sensors[1][sensor_id]['description']
        unit = available_sensors[1][sensor_id]['unit']

        return {'description': human_readable_name, 'value': LatestDataView._get_presented_value(last_value, unit)}

    @staticmethod
    def _get_presented_value(last_value, unit):
        if unit == '%' or unit == '°':
            presented_value = f'{last_value}{unit}'
        else:
            presented_value = f'{last_value} {unit}'
        return presented_value

    def get_initial(self):
        initial = super().get_initial()
        if 'station_id' not in self.kwargs:
            backend_proxy = CachedBackendProxy(BACKEND_URL, BACKEND_PORT, BACKEND_DO_USE_HTTPS)
            initial['station'] = backend_proxy.available_stations()[0][-1]['value']
        else:
            initial['station'] = self.kwargs['station_id']

        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        backend_proxy = CachedBackendProxy(BACKEND_URL, BACKEND_PORT, BACKEND_DO_USE_HTTPS)
        initial_dropdown_settings = []
        for entry in backend_proxy.available_stations()[0]:
            initial_dropdown_settings.append((entry['value'], entry['label']))
        kwargs['station_choices'] = initial_dropdown_settings

        return kwargs

    def form_valid(self, form):
        return HttpResponseRedirect(
            reverse('weatherpage:latest_station', kwargs={'station_id': form.data['station']}))
