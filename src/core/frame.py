from core.util import Logger
from data.data import SonicRawConverter, AmmoniaRawConverter, FpModelInitiator, EPProxy
import json
import pandas as pd


class BaseProcessModule:
    def __init__(self, prj_config: dict, mod_config: dict, logger: Logger):
        self.n_cores = prj_config['number_of_cores']
        self._logger = logger
        self._mod_config = mod_config
        self._parse_config()

    def _parse_config(self):
        raise NotImplementedError


class Project:

    def __init__(self):
        self._configs = None
        self.logger = Logger(log_path='')
        self._alias = None  # load_config
        self._n_cores = None  # load_config
        self._periods = None  # load_config

        self.ammonia_raw_prep = pd.DataFrame()

    def load_config(self, config_path='configs.json'):
        try:
            with open(config_path, 'r') as configs_file:
                self._configs = json.load(configs_file)
                self._parse_config()
        except:
            pass

    def _parse_config(self):
        try:
            self.prj_conf = self._configs['project_config']
            self.src_conf = self._configs['sonic_raw_convert_config']
            self.arc_conf = self._configs['ammonia_raw_convert_config']
            self.fmi_conf = self._configs['fp_model_init_config']
            self.epp_conf = self._configs['eddypro_proxy_config']
        except Exception as e:
            self.logger.log('Error occurred!' + str(e))

    def _check_config(self):
        try:
            self._alias = self.prj_conf["alias"]
            self._n_cores = self.prj_conf["n_cores"]
        except Exception as e:
            self.logger.log('Error occurred!' + str(e))

    def prepare_raw_data(self):
        sonic_raw_prep = SonicRawConverter(self.prj_conf, self.src_conf, self.logger)
        sonic_raw_prep.load_raw_data()
        sonic_raw_prep.prepare_sonic_data()
        ammonia_raw_prep = AmmoniaRawConverter(self.prj_conf, self.arc_conf, self.logger)
        ammonia_raw_prep.load_raw_data()
        ammonia_raw_prep.prepare_ammonia_data()

    def generate_turb_stats(self):
        ep_proxy = EPProxy()
        ep_proxy.modify_and_run()

    def initialize_fp_model(self):
        fp_init = FpModelInitiator(self.fmi_conf, self.logger)
        fp_init.initialize_model()
