from collections import namedtuple

from core.base import BaseModule


class FpGrdGenerator(BaseModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _parse_config(self):
        fmi_config = namedtuple('fmi_config', ['fpout_dir',
                                               'epr_dir',
                                               'cli_path',
                                               'z_m',
                                               'z_0',
                                               'x_max',
                                               'y_max',
                                               'dx',
                                               'loc_x',
                                               'loc_y'])
        self.config = fmi_config(self._mod_config['footprint_output_directory'],
                                 self._mod_config['eddypro_results_directory'],
                                 self._mod_config['footprint_model_cli_path'],
                                 self._mod_config['measure_height'],
                                 self._mod_config['roughness_height'],
                                 self._mod_config['x_range'],
                                 self._mod_config['y_range'],
                                 self._mod_config['grid_size'],
                                 self._mod_config['station_x'],
                                 self._mod_config['station_y'])

    def initialize_and_run(self):
        @self._logger.log_process('Generate Footprint Grid Files')
        def process():
            self._initialize_fp_model()

        process()

    def _initialize_fp_model(self):
        raise NotImplementedError

    def _run_fp_model(self):
        raise NotImplementedError


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
