import sys
from configparser import ConfigParser

from core.rawcvt import SonicRawConverter, AmmoniaRawConverter
from util.logger import logger
from core.plot import TimeSeriesPlotter
from core.cftpp import FpGrdGeneratorClassic
from core.epproxy import EPProxy


class Project:
    def __init__(self):
        self._config = None
        self._set = False
        self.logger = logger

    def init(self, config_path='configs.ini'):
        self._config = ConfigParser()
        while True:
            try:
                self._config.read(config_path)
                if self._config.get('Project', 'Project_Name'):
                    self._set = True
                    break
                else:
                    raise ValueError('Invalid config file')

            except Exception as e:
                print(e)
                config_path = input('Loading config file failed, CHECK and enter config file name:')

    def set_log_path(self, log_path: str):
        self.logger.set_log_path(log_path)

    def prepare_sonic_data(self):
        if not self._set:
            print('Project not initialized, CHECK script!')
            sys.exit(1)
        srp = SonicRawConverter(config=self._config, logger=logger)
        srp.load_raw_data()
        srp.convert_sonic_data()

    def prepare_ammonia_data(self):
        if not self._set:
            print('Project not initialized, CHECK script!')
            sys.exit(1)
        arp = AmmoniaRawConverter(config=self._config, logger=logger)
        arp.load_raw_data()
        arp.prepare_ammonia_data()

    def generate_turb_stats(self):
        if not self._set:
            print('Project not initialized, CHECK script!')
            sys.exit(1)
        ep_proxy = EPProxy(config=self._config, logger=logger)
        ep_proxy.modify_and_run()

    def generate_fp_grds(self, method='classic'):
        if not self._set:
            print('Project not initialized, CHECK script!')
            sys.exit(1)
        if method == 'classic':
            fp_init = FpGrdGeneratorClassic(config=self._config, logger=logger)
            fp_init.initialize_and_run()
        elif method == 'new':
            pass  # TODO
        else:
            raise ValueError('Invalid method type')

    def plot_timeseries(self):
        if not self._set:
            print('Project not initialized, CHECK script!')
            sys.exit(1)
        ts_plotter = TimeSeriesPlotter(config=self._config, logger=logger)
        ts_plotter.plot_summary()
        # ts_plotter.plot_daily_ts()
        # ts_plotter.plot_hourly_box()
