from core import file as fl
from core.file import get_path
from modules.data import BaseDataModule
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import pandas as pd
import datetime
from collections import namedtuple

import json
import os


class Plotter(BaseDataModule):
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
        pass

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
        plot_order = ['wind_speed', 'wind_dir', 't_air', 'rh_air', 'H']
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


def load_project_config(config_file):
    useful_items = ['proj_periods', 'proj_path', 'analyses_sub', 'n_cores']
    with open(config_file, 'r') as config:
        project_config = json.load(config)
        project_config_useful = {item: project_config[item] for item in project_config if item in useful_items}
    return project_config_useful


def load_plot_config(config_file):
    with open(config_file, 'r') as config:
        plot_config = json.load(config)
    return plot_config


class PlotData:
    def __init__(self,
                 proj_periods: dict,
                 proj_path: str,
                 analyses_sub: str,
                 n_cores: int,
                 plot_order: list,
                 plot_settings: dict
                 ):
        self.start_time = proj_periods['start']
        self.end_time = proj_periods['end']
        self.data_path = fl.get_path(target_dir=proj_path + analyses_sub, file_init='eddypro_ADV_full_output',
                                     file_ext='.csv')
        self.plot_path = proj_path + analyses_sub + '\\Plots\\'
        self.plot_order = plot_order
        self.load_order = ['date', 'time'] + self.plot_order
        self.plot_settings = plot_settings

        self._load_data()

    def _load_data(self):
        self.data = pd.read_csv(self.data_path, skiprows=[0, 2], usecols=self.load_order, parse_dates=[[0, 1]],
                                na_values=-9999)
        self.data.set_index(self.data.columns[0], inplace=True)
        self.data = self.data[self.start_time: self.end_time]
        self.subs = self.data.shape[1]
        assert (self.subs < 10)
        self.fig_size = (len(self.data) // 77, self.subs * 3)
        assert self.subs <= len(self.plot_settings)

    @staticmethod
    def get_pos(sub: str, order: list):
        return int("%s1%s" % (len(order), order.index(sub) + 1))  # e.g.312 means 2nd row of 3 in single column

    def multi_plot(self):
        multi_plot = plt.figure(figsize=self.fig_size, dpi=300)
        for sub_name in self.plot_order:
            sub_plot = multi_plot.add_subplot(self.get_pos(sub_name, self.plot_order),
                                              ylim=self.plot_settings[sub_name]['ylim'])
            plt.plot(self.data[sub_name], self.plot_settings[sub_name]['style'],
                     **self.plot_settings[sub_name]['params'])

            sub_plot.tick_params(axis='both', direction='in', labelsize=14)

            sub_plot.xaxis.set_major_formatter(dates.DateFormatter('%m/%d'))
            sub_plot.xaxis.set_major_locator(dates.DayLocator())
            sub_plot.set_xlabel('Date', fontsize=18)

            sub_plot.set_ylabel(self.plot_settings[sub_name]['label'], fontsize=18)
            sub_plot.yaxis.set_major_locator(plt.FixedLocator(self.plot_settings[sub_name]['y_ticks']))

        multi_plot.tight_layout()
        os.makedirs(self.plot_path, exist_ok=True)
        plt.savefig(self.plot_path + 'ADV.png')
        plt.close(multi_plot)
