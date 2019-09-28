import file
from modules import BaseDataModule
import os
from collections import namedtuple
import pandas as pd
import numpy as np


class GRDAnalyzer(BaseDataModule):

    def _parse_config(self):
        grd_config = namedtuple('grd_config', ['grd_dir', 'gl_dir'])
        self.config = grd_config(self._mod_config['grd_files_directory'],
                                 self._mod_config['group_lists_directory'])

    def _group_by_custom(self):
        custom_groups = {}
        group_lists = file.get_paths(target_dir=self.config.gl_dir, file_ext='.txt')  #
        for group_list in group_lists:
            group_code = os.path.split(group_list)[-1]
            custom_groups[group_code] = []
            with open(group_list, 'r') as gl:
                for group_member_name in gl:
                    group_member_path = file.get_path(target_dir=self.grd_paths, file_init=group_member_name)
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
        self.grd_paths = file.get_paths(target_dir=self.config.grd_dir, file_ext='.grd')

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


def grid_average(grid_groups, output_dir: str):
    for grid_group in grid_groups:
        average_grid = pd.DataFrame()
        i = 0
        for grid_file in grid_groups[grid_group]:
            if i == 0:
                average_grid = pd.read_csv(grid_file, skiprows=list(range(4)), sep='\s+', header=None, index_col=False)
            else:
                average_grid += pd.read_csv(grid_file, skiprows=list(range(4)), sep='\s+', header=None,
                                            index_col=False)
            i += 1
        average_grid /= i
        os.makedirs(output_dir, exist_ok=True)
        out_path = output_dir + '\\' + grid_group + '.grd'
        average_grid.to_csv(out_path, sep=' ', header=False, index=False)
        with open(out_path, 'r+') as f:
            content = f.read()
            f.seek(0, 0)
            f.write('DSAA\n150 150\n0 0.7500001\n0 0.7500001\n0 1.000000\n' + content)
