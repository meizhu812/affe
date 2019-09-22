from core.util import Logger
from modules.data import SonicRawConverter, AmmoniaRawConverter, FpGrdGeneratorClassic, EPProxy
from modules.plot import Plotter
import json


class Project:

    def __init__(self):
        self._configs = None
        self.logger = Logger(log_path='')
        self._alias = None  # load_config
        self._n_cores = None  # load_config
        self._periods = None  # load_config

    def load_configs(self, config_path='configs.json'):
        @self.logger.log_process('Loading Configs', timed=False)
        def process():
            try:
                with open(config_path, 'r') as configs_file:
                    self._configs = json.load(configs_file)
                    self._parse_config()
            except:
                pass

        process()

    def _parse_config(self):
        try:
            self.prj_conf = self._configs['project_config']
            self.src_conf = self._configs['sonic_raw_convert_config']
            self.arc_conf = self._configs['ammonia_raw_convert_config']
            self.epp_conf = self._configs['eddypro_proxy_config']
            self.fme_conf = self._configs['fp_model_executor_config']
            self.tsp_conf = self._configs['timeseries_plotter_config']
        except Exception as e:
            self.logger.log('Error occurred!' + str(e))

    def _check_config(self):
        try:
            self._alias = self.prj_conf["alias"]
            self._n_cores = self.prj_conf["n_cores"]
        except Exception as e:
            self.logger.log('Error occurred!' + str(e) + '\n')

    def prepare_raw_data(self):
        sonic_raw_prep = SonicRawConverter(self.prj_conf, self.src_conf, self.logger)
        sonic_raw_prep.load_raw_data()
        sonic_raw_prep.convert_sonic_data()
        ammonia_raw_prep = AmmoniaRawConverter(self.prj_conf, self.arc_conf, self.logger)
        ammonia_raw_prep.load_raw_data()
        ammonia_raw_prep.prepare_ammonia_data()

    def generate_turb_stats(self):
        ep_proxy = EPProxy(self.prj_conf, self.epp_conf, self.logger)
        ep_proxy.modify_and_run()

    def generate_fp_grds(self, method='classic'):
        if method == 'classic':
            fp_init = FpGrdGeneratorClassic(self.prj_conf, self.fme_conf, self.logger)
            fp_init.initialize_and_run()
        elif method == 'new':
            pass  # TODO
        else:
            raise ValueError('Invalid method type')

    def plot_timeseries(self):
        ts_plotter = Plotter(self.prj_conf, self.tsp_conf, self.logger)
        ts_plotter.plot_summary()


