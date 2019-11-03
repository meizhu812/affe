from collections import namedtuple

from core.base import BaseModule


class FpGrdGenerator(BaseModule):

    def _parse_config(self):
        raise NotImplementedError

    def initialize_and_run(self):
        @self._logger.log_process('Generate Footprint Grid Files')
        def process():
            self._initialize_fp_model()
            self._run_fp_model()
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
