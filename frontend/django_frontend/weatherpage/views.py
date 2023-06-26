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

from os import environ
from django.shortcuts import render

# noinspection PyUnresolvedReferences
from . import dash_weatherpage_app
# noinspection PyUnresolvedReferences
from . import dash_download_page_app


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
