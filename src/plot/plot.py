# coding=utf-8
from core import file as fl
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import pandas as pd

import json
import os
#
# @dataclass
# class PlotData:
#     # path: str
#     config: dict
#     data: pd.DataFrame


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
        self.data_path = fl.get_path(target_dir=proj_path+analyses_sub, file_init='eddypro_ADV_full_output', file_ext='.csv')
        self.plot_path = proj_path+analyses_sub+'\\Plots\\'
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
        return int("%s1%s" % (len(order), order.index(sub)+1))  # e.g.312 means 2nd row of 3 in single column

    def multi_plot(self):
        multi_plot = plt.figure(figsize=self.fig_size, dpi=300)
        for sub_name in self.plot_order:
            sub_plot = multi_plot.add_subplot(self.get_pos(sub_name, self.plot_order),
                                              ylim=self.plot_settings[sub_name]['ylim'])
            plt.plot(self.data[sub_name], self.plot_settings[sub_name]['style'], **self.plot_settings[sub_name]['params'])

            sub_plot.tick_params(axis='both', direction='in', labelsize=14)

            sub_plot.xaxis.set_major_formatter(dates.DateFormatter('%m/%d'))
            sub_plot.xaxis.set_major_locator(dates.DayLocator())
            sub_plot.set_xlabel('Date', fontsize=18)

            sub_plot.set_ylabel(self.plot_settings[sub_name]['label'], fontsize=18)
            sub_plot.yaxis.set_major_locator(plt.FixedLocator(self.plot_settings[sub_name]['y_ticks']))

        multi_plot.tight_layout()
        os.makedirs(self.plot_path,exist_ok=True)
        plt.savefig(self.plot_path+'ADV.png')
        plt.close(multi_plot)
