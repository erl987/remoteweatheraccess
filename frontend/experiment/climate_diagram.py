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

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio
from matplotlib import pyplot as plt
from plotly.subplots import make_subplots

pio.renderers.default = "browser"

STATION_IDS = ['ECK', 'SOL']
FILE_BASE_DIR = './data'

LOCALE = 'de_DE.UTF-8'
TEMP_AXIS_TICK_REFERENCE = 5
RAIN_AXIS_TICK_REFERENCE = 50

DIAGRAM_FONT_SIZE = 18
DIAGRAM_FONT_FAMILY = 'Helvetica Neue, Helvetica, Arial, sans-serif'  # default for Bootstrap
DIAGRAM_LINE_WIDTH = 2
DIAGRAM_MARKER_SIZE = 12
COLOR_TEMP = '#DF382C'  # red
COLOR_RAIN = '#007bff'  # blue
GRID_COLOR = '#a5b1cd'  # grey


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


def plot_matplotlib(mean_rain_by_month, mean_temps_by_month, month_names_short, station_id):
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


def plot_plotly(mean_rain_by_month, mean_temps_by_month, month_names_short):
    df_rain_plot = pd.DataFrame(dict(
        x=month_names_short,
        y=mean_rain_by_month
    ))
    df_temp_plot = pd.DataFrame(dict(
        x=month_names_short,
        y=mean_temps_by_month
    ))

    fig = make_subplots(specs=[[{'secondary_y': True}]])

    fig.add_trace(px.bar(df_rain_plot, x='x', y='y').data[0], secondary_y=False)
    fig.update_yaxes(showline=True,
                     linewidth=DIAGRAM_LINE_WIDTH,
                     title_text='Regen / mm',
                     title_font_size=DIAGRAM_FONT_SIZE,
                     title_font_family=DIAGRAM_FONT_FAMILY,
                     tickfont_size=DIAGRAM_FONT_SIZE,
                     tickfont_family=DIAGRAM_FONT_FAMILY,
                     linecolor=COLOR_RAIN,
                     color=COLOR_RAIN,
                     showgrid=True,
                     gridcolor=GRID_COLOR,
                     secondary_y=False)
    fig.update_traces(marker_color=COLOR_RAIN,
                      hovertemplate='%{y:.0f}',
                      hoverlabel_font_family=DIAGRAM_FONT_FAMILY,
                      hoverlabel_font_size=DIAGRAM_FONT_SIZE,
                      secondary_y=False)

    if mean_rain_by_month.max() > 0:
        fig.update_layout(yaxis_range=[0, round_up_to_next(mean_rain_by_month.max(), RAIN_AXIS_TICK_REFERENCE)])

    fig.add_trace(px.line(df_temp_plot, x='x', y='y').data[0], secondary_y=True)
    fig.update_yaxes(showline=True,
                     linewidth=DIAGRAM_LINE_WIDTH,
                     title_text='Temperatur / \N{DEGREE SIGN}C',
                     title_font_size=DIAGRAM_FONT_SIZE,
                     title_font_family=DIAGRAM_FONT_FAMILY,
                     tickfont_size=DIAGRAM_FONT_SIZE,
                     tickfont_family=DIAGRAM_FONT_FAMILY,
                     linecolor=COLOR_TEMP,
                     color=COLOR_TEMP,
                     showgrid=False,
                     range=[
                         round_down_to_next(mean_temps_by_month.min(), TEMP_AXIS_TICK_REFERENCE),
                         round_up_to_next(mean_temps_by_month.max(), TEMP_AXIS_TICK_REFERENCE)
                     ],
                     secondary_y=True)
    fig.update_traces(line_color=COLOR_TEMP,
                      line_width=DIAGRAM_LINE_WIDTH,
                      mode='lines+markers',
                      marker=dict(size=DIAGRAM_MARKER_SIZE),
                      hovertemplate='%{y:.1f}',
                      hoverlabel_font_family=DIAGRAM_FONT_FAMILY,
                      hoverlabel_font_size=DIAGRAM_FONT_SIZE,
                      secondary_y=True)

    fig.update_xaxes(showgrid=False,
                     linecolor='black',
                     linewidth=DIAGRAM_LINE_WIDTH,
                     tickfont_size=DIAGRAM_FONT_SIZE,
                     tickfont_family=DIAGRAM_FONT_FAMILY)
    fig.update_layout(plot_bgcolor='white', hovermode='x'),

    fig.show()


def main():
    locale.setlocale(locale.LC_TIME, LOCALE)

    all_dfs = read_for_stations(STATION_IDS, FILE_BASE_DIR)

    for station_id in STATION_IDS:
        df = all_dfs[station_id]
        monthly_average_temp = df['Temperatur (Außensensor 1)'].resample('D').mean().resample('M').mean()
        mean_temps_by_month = monthly_average_temp.groupby(monthly_average_temp.index.month).mean()

        monthly_rain_sum = df['Regenrate'].resample('M').sum()
        mean_rain_by_month = monthly_rain_sum.groupby(monthly_rain_sum.index.month).mean()

        month_names_short = [month_abbr[m] for m in mean_temps_by_month.index]

        plot_plotly(mean_rain_by_month, mean_temps_by_month, month_names_short)
        plot_matplotlib(mean_rain_by_month, mean_temps_by_month, month_names_short, station_id)


if __name__ == '__main__':
    main()
