from pandas import DataFrame, read_csv
import numpy as np
from core.file import get_paths
from core.frame import BaseProcessModule
from os import path
from collections import namedtuple


class GRDAnalyzer(BaseProcessModule):

    def _parse_config(self):
        grd_config = namedtuple('grd_config', ['grd_dir'])
        self._config = grd_config(self._mod_config['raw_files_directory'])

    def _group_by_custom(self):
        pass

    def _group_by_hour(self):
        hour_groups = {'{:0>2d}'.format(int(b)): [] for b in list(np.linspace(0, 23, 24))}  # from '00' to '23'
        for grd_path in self.grd_paths:
            grd_name = path.splitext(path.split(grd_path)[1])[0]
            hour_code = grd_name[6:8]
            hour_groups[hour_code].append(grd_path)
        return hour_groups

    def _get_grd_paths(self):
        self.grd_paths = get_paths(target_dir=self._config.grd_dir, file_ext='.grd')

    def group_by_day(self):
        pass


class GrGrouper:
    def __init__(self):
        self.grd


def grid_file_grouping(grid_files: list, key_name: str, key_loc: slice, grid_groups: dict):
    for grid_file in grid_files:
        grid_file[key_name] = grid_file['path'].split('\\')[-1][key_loc]  # TODO
        for grid_group in grid_groups:
            if not grid_file[key_name] in grid_group:
                grid_groups[grid_file[key_name]] = []  # create new group
            grid_groups[grid_file[key_name]].append(grid_file['path'])
    return grid_groups


def grid_average(grid_groups, output_dir: str):
    for grid_group in grid_groups:
        average_grid = DataFrame
        i = 0
        for grid_file in grid_groups[grid_group]:
            if i == 0:
                average_grid = read_csv(grid_file, skiprows=[0, 1, 2, 3, 4], sep='\s+', header=None, index_col=False)
            else:
                average_grid += read_csv(grid_file, skiprows=[0, 1, 2, 3, 4], sep='\s+', header=None,
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
