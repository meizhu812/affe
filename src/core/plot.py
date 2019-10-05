import datetime
import os
from collections import namedtuple

import pandas as pd
from matplotlib import pyplot as plt, dates as dates

from core.base import BaseModule
from core.file import get_path


class Plotter(BaseModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._load_data()

    def _parse_config(self):
        tsp_config = namedtuple('tsp_config', ['stat_dir',
                                               'amd_path',
                                               'plot_path',
                                               'plot_settings'])
        self.config = tsp_config(self._mod_config['meteorology_statistics_directory'],
                                 self._mod_config['ammonia_data_path'],
                                 self._mod_config['plot_path'],
                                 self._mod_config['plot_settings'])

    def _load_data(self):
        result_path = get_path(target_dir=self.config.stat_dir,
                               file_init='eddypro_ADV_essentials',
                               file_ext='adv.csv')
        useful_cols = ['date',
                       'time',
                       'wind_dir',
                       'wind_speed',
                       'H',
                       't_air',
                       'rh_air']
        met_data = pd.read_csv(result_path,
                               usecols=useful_cols,
                               parse_dates=[[0, 1]],
                               na_values=-9999)
        met_data.set_index(met_data.columns[0], inplace=True)
        am_data = pd.read_csv(self.config.amd_path, parse_dates=[0])
        am_data.set_index(am_data.columns[0], inplace=True)
        self.data = am_data.join(met_data)
        self.data['T'] = self.data['t_air'] - 273.15
        self.data.drop('t_air', axis=1)

    def plot_windrose(self):
        pass

    def plot_hourly_box(self):
        plot_order = ['wind_speed', 'wind_dir', 'T', 'H']
        hours = list(range(24))
        hourly_data = self.data.resample('H').mean()
        hourly_data['hour'] = hourly_data.index.hour
        for plot_item in plot_order:
            plot_data = {}
            for hour in hours:
                plot_data[hour] = list(pd.Series(hourly_data[hourly_data['hour'] == hour][plot_item]).values)
            plot_data = pd.DataFrame.from_dict(plot_data, orient='index').transpose()
            print(plot_data)

    def plot_summary(self):
        fig_size = (30, 20)
        multi_plot = plt.figure(figsize=fig_size, dpi=300)
        plot_order = ['wind_speed', 'wind_dir', 'T', 'rh_air', 'H']
        for sub_name in plot_order:
            sub_plot = multi_plot.add_subplot(self._get_pos(sub_name, plot_order),
                                              xlim=[self.data.index[0].date(), self.data.index[-1].date()],
                                              ylim=self.config.plot_settings[sub_name]['ylim'])
            plt.plot(self.data[sub_name], self.config.plot_settings[sub_name]['style'],
                     **self.config.plot_settings[sub_name]['params'])

            sub_plot.tick_params(axis='both', length=10, which='major', direction='in', labelsize=14)

            sub_plot.xaxis.set_major_formatter(dates.DateFormatter('%m/%d'))
            sub_plot.xaxis.set_major_locator(dates.DayLocator())
            sub_plot.set_xlabel('Date', fontsize=18)

            sub_plot.set_ylabel(self.config.plot_settings[sub_name]['label'], fontsize=18)
            sub_plot.yaxis.set_major_locator(plt.FixedLocator(self.config.plot_settings[sub_name]['y_ticks']))

        # multi_plot.tight_layout()
        os.makedirs(self.config.plot_path, exist_ok=True)
        plt.savefig(self.config.plot_path + '\\all_ADV.png')
        plt.close(multi_plot)

    def plot_daily_ts(self):
        data_range = pd.date_range(self.data.index[0].date(), self.data.index[-1].date() + datetime.timedelta(days=1))
        daily_data = []
        for n in range(len(data_range) - 1):
            daily_data.append(self.data[data_range[n]:data_range[n + 1]])
        for data in daily_data:
            print(data.describe())
            try:
                self._plot_daily_ts(data)
            except Exception as e:
                print('err {}'.format(e))

    @staticmethod
    def _get_pos(sub: str, order: list):
        return int("%s1%s" % (len(order), order.index(sub) + 1))  # e.g.312 means 2nd row of 3 in single column

    def _plot_daily_ts(self, data):
        fig_size = (14, 20)
        multi_plot = plt.figure(figsize=fig_size, dpi=300)
        plot_order = ['wind_speed', 'wind_dir', 'T', 'rh_air', 'H']
        for sub_name in plot_order:
            sub_plot = multi_plot.add_subplot(self._get_pos(sub_name, plot_order),
                                              xlim=[data.index[0].date(), data.index[-1].date()],
                                              ylim=self.config.plot_settings[sub_name]['ylim'])
            plt.plot(data[sub_name], self.config.plot_settings[sub_name]['style'],
                     **self.config.plot_settings[sub_name]['params'])

            sub_plot.tick_params(axis='both', length=10, which='major', direction='in', labelsize=14)
            sub_plot.tick_params(axis='both', length=5, which='minor', direction='in', labelsize=14)

            sub_plot.xaxis.set_major_formatter(dates.DateFormatter('%m/%d'))
            sub_plot.xaxis.set_major_locator(dates.DayLocator())
            sub_plot.xaxis.set_minor_locator(dates.HourLocator())
            sub_plot.set_xlabel('Date', fontsize=18)

            sub_plot.set_ylabel(self.config.plot_settings[sub_name]['label'], fontsize=18)
            sub_plot.yaxis.set_major_locator(plt.FixedLocator(self.config.plot_settings[sub_name]['y_ticks']))

        # multi_plot.tight_layout()
        os.makedirs(self.config.plot_path, exist_ok=True)
        plt.savefig(self.config.plot_path + '\\' + str(data.index[0].date()) + 'ADV.png')
        plt.close(multi_plot)