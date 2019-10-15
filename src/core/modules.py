from collections import namedtuple

from core.base import BaseModule


class FluxEstimator(BaseModule):
    def _parse_config(self):
        fe_config = namedtuple('fe_config', ['fc_N_path',
                                             'C_N_path',
                                             'fc_S_path',
                                             'C_S_path'])
        self.config = fe_config(self._mod_config['north_fcsum_file_path'],
                                self._mod_config['north_conc_file_path'],
                                self._mod_config['south_fcsum_file_path'],
                                self._mod_config['south_conc_file_path'])
