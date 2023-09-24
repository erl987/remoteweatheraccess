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

from datetime import datetime, timedelta, timezone
from locale import format_string
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

    SPECIAL_SENSOR_IDS = ['direction', 'gusts', 'rain_last_hour', 'speed', 'wind_temperature', 'uv']
    GENERAL_SENSOR_ORDER = ['temperature', 'humidity', 'rain', 'dewpoint']

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        station_id = self.kwargs.get('station_id', None)

        backend_proxy = CachedBackendProxy(BACKEND_URL, BACKEND_PORT, BACKEND_DO_USE_HTTPS)
        if not station_id:
            station_id = self._get_sorted_stations(backend_proxy)[-1]['value']
        available_sensors = self._get_available_sensors(backend_proxy)
        latest_data = backend_proxy.latest_data()

        if len(latest_data) > 0:
            sensor_data, special_sensor_data = self._get_human_readable_sensor_data(available_sensors, latest_data,
                                                                                    station_id)

            time_point = datetime.fromisoformat(latest_data[station_id]['timepoint'])

            context['time_point'] = time_point
            context['sensor_data'] = sorted(sensor_data, key=lambda d: d['description'])
            context['special_sensor_data'] = sorted(special_sensor_data, key=lambda d: d['description'])
            context['status'] = self._get_transmission_status(time_point)

        return context

    @staticmethod
    def _get_transmission_status(time_point):
        if (datetime.now(timezone.utc) - time_point) <= timedelta(minutes=10):
            return 'current'
        elif (datetime.now(timezone.utc) - time_point) <= timedelta(hours=1):
            return 'delayed'
        else:
            return 'interrupted'

    @staticmethod
    def _get_available_sensors(backend_proxy):
        available_sensors = backend_proxy.available_sensors()

        available_sensors[1]['rain_last_day'] = {'description': 'Regen (letzte 24 Stunden)', 'unit': 'mm'}
        available_sensors[1]['rain_last_hour'] = {'description': 'Regen (letzte Stunde)', 'unit': 'mm'}

        return available_sensors

    def _get_human_readable_sensor_data(self, available_sensors, latest_data, station_id):
        sensor_data = []
        special_sensor_data = []

        for sensor_id, value in latest_data[station_id].items():
            if sensor_id == 'timepoint':
                continue

            if sensor_id == 'temperature_humidity':
                for temp_humid_sensor_id, subsensors in value.items():
                    for subsensor_id, sub_value in subsensors.items():
                        sensor_data.append(self._get_subsensor_data(subsensor_id, temp_humid_sensor_id, sub_value,
                                                                    available_sensors))
            else:
                this_sensor_data = self._get_sensor_data(sensor_id, value, available_sensors)
                self._replace_sensor_descriptions(this_sensor_data)

                if sensor_id not in LatestDataView.SPECIAL_SENSOR_IDS:
                    sensor_data.append(this_sensor_data)
                else:
                    special_sensor_data.append(this_sensor_data)

        return sensor_data, special_sensor_data

    @staticmethod
    def _replace_sensor_descriptions(this_sensor_data):
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
        if last_value is None:
            presented_value = '-'
        else:
            if unit == '%' or unit == '°':
                presented_value = f'{format_string("%.1f", last_value)}{unit}'
            else:
                presented_value = f'{format_string("%.1f", last_value)} {unit}'

        return presented_value

    def get_initial(self):
        initial = super().get_initial()
        if 'station_id' not in self.kwargs:
            backend_proxy = CachedBackendProxy(BACKEND_URL, BACKEND_PORT, BACKEND_DO_USE_HTTPS)
            stations = self._get_sorted_stations(backend_proxy)
            initial['station'] = stations[-1]['value']
        else:
            initial['station'] = self.kwargs['station_id']

        return initial

    @staticmethod
    def _get_sorted_stations(backend_proxy):
        return sorted(backend_proxy.available_stations()[0], key=lambda d: d['label'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        backend_proxy = CachedBackendProxy(BACKEND_URL, BACKEND_PORT, BACKEND_DO_USE_HTTPS)
        initial_dropdown_settings = []
        for entry in self._get_sorted_stations(backend_proxy):
            initial_dropdown_settings.append((entry['value'], entry['label']))
        kwargs['station_choices'] = initial_dropdown_settings

        return kwargs

    def form_valid(self, form):
        return HttpResponseRedirect(reverse('weatherpage:latest_station', kwargs={'station_id': form.data['station']}))
