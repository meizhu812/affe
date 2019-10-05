import os
from collections import namedtuple

import numpy as np
from matplotlib import pyplot as plt

from core.base import BaseModule
from core.file import get_paths, get_path


class FpGrdProcessor(BaseModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _parse_config(self):
        pass

    @staticmethod
    def _plot_grd(grd_data, grd_path):
        plt.contourf(grd_data)
        plt.savefig(os.path.splitext(grd_path)[0] + '.png', dpi=300)


class GRDAnalyzer(BaseModule):

    def _parse_config(self):
        grd_config = namedtuple('grd_config', ['grd_dir', 'gl_dir'])
        self.config = grd_config(self._mod_config['grd_files_directory'],
                                 self._mod_config['group_lists_directory'])

    def _group_by_custom(self):
        custom_groups = {}
        group_lists = get_paths(target_dir=self.config.gl_dir, file_ext='.txt')  #
        for group_list in group_lists:
            group_code = os.path.split(group_list)[-1]
            custom_groups[group_code] = []
            with open(group_list, 'r') as gl:
                for group_member_name in gl:
                    group_member_path = get_path(target_dir=self.grd_paths, file_init=group_member_name)
                    custom_groups[group_code].append(group_member_path)
        return custom_groups

    def _group_by_hour(self):
        hour_groups = {'{:0>2d}'.format(int(b)): [] for b in list(np.linspace(0, 23, 24))}  # from '00' to '23'
        for grd_path in self.grd_paths:
            grd_name = os.path.splitext(os.path.split(grd_path)[1])[0]
            hour_code = grd_name[6:8]
            hour_groups[hour_code].append(grd_path)
        return hour_groups

    def _get_grd_paths(self):
        self.grd_paths = get_paths(target_dir=self.config.grd_dir, file_ext='.grd')

    def _group_by_day(self):
        day_groups = {}
        for grd_path in self.grd_paths:
            grd_name = os.path.splitext(os.path.split(grd_path)[1])[0]
            day_code = grd_name[0:6]
            if day_code in day_groups:
                day_groups[day_code].append(grd_path)
            else:
                day_groups[day_code] = [grd_path]  # create new day key
        return day_groups