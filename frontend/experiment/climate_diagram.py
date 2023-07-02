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

import locale
import os
from calendar import month_abbr
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

STATION_IDS = ['ECK', 'SOL']
FILE_BASE_DIR = './data'


# TODO: handle missing data
# TODO: provide error bars
# TODO: connect to REST-API


def read_for_stations(station_ids, file_base_dir) -> Dict[str, pd.DataFrame]:
    data_for_stations = {}
    for station_id in station_ids:
        all_dfs = []
        data_dir_path = os.path.join(file_base_dir, station_id)
        for file in os.listdir(data_dir_path):
            file_path = str(os.path.join(data_dir_path, file))

            if not file_path.lower().endswith('.csv'):
                continue

            df = pd.read_csv(file_path, skiprows=[1, 2, 3])
            df['Zeitpunkt'] = pd.to_datetime(df['Datum'] + ' ' + df['Uhrzeit'], format='%d.%m.%Y %H:%M')
            df = df.set_index('Zeitpunkt')
            df = df.drop(columns=['Datum', 'Uhrzeit'])

            all_dfs.append(df)

        data_for_stations[station_id] = pd.concat(all_dfs).sort_index()

    return data_for_stations


def round_up_to_next(value, reference):
    return reference * np.ceil(value / reference)


def round_down_to_next(value, reference):
    return reference * np.floor(value / reference)


def main():
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')

    all_dfs = read_for_stations(STATION_IDS, FILE_BASE_DIR)

    for station_id in STATION_IDS:
        df = all_dfs[station_id]
        monthly_average_temp = df['Temperatur (Außensensor 1)'].resample('D').mean().resample('M').mean()
        mean_temps_by_month = monthly_average_temp.groupby(monthly_average_temp.index.month).mean()

        monthly_rain_sum = df['Regenrate'].resample('M').sum()
        mean_rain_by_month = monthly_rain_sum.groupby(monthly_rain_sum.index.month).mean()

        month_names_short = [month_abbr[m] for m in mean_temps_by_month.index]

        plt.figure()
        plt.title(f'Klimadiagramm Station {station_id}')
        plt.bar(month_names_short, mean_rain_by_month)
        ax_rain = plt.gca()
        ax_rain.set_ylabel('Regen / mm')
        ax_rain.yaxis.label.set_color('blue')
        ax_rain.tick_params(axis='y', colors='blue')
        ax_rain.spines['left'].set_color('blue')
        if mean_rain_by_month.max() > 0:
            ax_rain.set_ylim([0, round_up_to_next(mean_rain_by_month.max(), 50)])

        ax_temp = ax_rain.twinx()
        ax_temp.plot(month_names_short, mean_temps_by_month, 'r')
        ax_temp.set_ylabel('Temperatur / \N{DEGREE SIGN}C')
        ax_temp.yaxis.label.set_color('red')
        ax_temp.tick_params(axis='y', colors='red')
        ax_temp.spines['right'].set_color('red')
        ax_temp.set_ylim([
            round_down_to_next(mean_temps_by_month.min(), 5),
            round_up_to_next(mean_temps_by_month.max(), 5)
        ])


if __name__ == '__main__':
    main()
