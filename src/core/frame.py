from core.util import Logger
from data.data import SonicRawConverter, AmmoniaRawConverter, FpModelInitiator, EPProxy
import json
import pandas as pd


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
            self.fmi_conf = self._configs['fp_model_initiator_config']
        except Exception as e:
            self.logger.log('Error occurred!' + str(e))

    def _check_config(self):
        try:
            self._alias = self.prj_conf["alias"]
            self._n_cores = self.prj_conf["n_cores"]
        except Exception as e:
            self.logger.log('Error occurred!' + str(e) + '\n')

    def prepare_raw_data(self):
        @self.logger.log_process('Processing Raw Data')
        def process():
            sonic_raw_prep = SonicRawConverter(self.prj_conf, self.src_conf, self.logger)
            sonic_raw_prep.load_raw_data()
            sonic_raw_prep.convert_sonic_data()
            ammonia_raw_prep = AmmoniaRawConverter(self.prj_conf, self.arc_conf, self.logger)
            ammonia_raw_prep.load_raw_data()
            ammonia_raw_prep.prepare_ammonia_data()

        process()

    def generate_turb_stats(self):
        ep_proxy = EPProxy(self.prj_conf, self.epp_conf)
        ep_proxy.modify_and_run()

    def initialize_fp_model(self):
        fp_init = FpModelInitiator(self.fmi_conf, self.logger)
        fp_init.initialize_model()
