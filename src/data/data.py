"""
doc
"""
import os
from core.frame import BaseProcessModule
from itertools import islice
from multiprocessing import Pool
from collections import namedtuple

import pandas as pd

from core.file import get_path, get_paths
from core.util import Console, ApplyProgressBar


class RawConverter(BaseProcessModule):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.raw_data = None
        self.temp_data = None

    def _parse_config(self):
        rc_config = namedtuple('rc_config', ['raw_dir',
                                             'cvt_dir',
                                             'raw_format',
                                             'raw_pattern',
                                             'data_periods'])
        self._config = rc_config(self._mod_config['raw_files_directory'],
                                 self._mod_config['converted_files_directory'],
                                 self._mod_config['raw_data_format'],
                                 self._mod_config['raw_filenames_pattern'],
                                 pd.date_range(**self._mod_config['data_periods_parameters']))

    def load_raw_data(self):
        file_paths = self._get_raw_paths(raw_dir=self._config.raw_dir, **self._config.raw_pattern)
        raw_data_async = self._get_raw_data(file_paths, self._config.raw_format)
        self.raw_data = self._merge_raw_data(raw_data_async)

    def _get_raw_paths(self, *args, **kwargs):
        @self._logger.log_action('Getting raw data files', timed=False)
        def action(*, raw_dir: str, file_init: str, file_ext: str):
            Console.output("Listing files in folder: [{}]\n".format(raw_dir))
            self._logger.log("[INIT]:'{}'\t".format(file_init) + "[EXT]:'{}'\n".format(file_ext))

            raw_paths = get_paths(target_dir=raw_dir, file_init=file_init, file_ext=file_ext)

            for raw_path in raw_paths[:3]:  # print heads
                self._logger.log(raw_path)
            self._logger.log(6 * '...')
            for raw_path in raw_paths[-3:]:  # print tails
                self._logger.log(raw_path)

            self._logger.log('[ {} ] files found.\n'.format(len(raw_paths)))
            self._logger.log('Check sequence of raw data files, press Enter to continue...\n')
            input()
            return raw_paths

        return action(*args, **kwargs)

    def _get_raw_data(self, *args, **kwargs):
        @self._logger.log_action('Getting [{}] data'.format('null'))
        def action(raw_paths: list, raw_format):
            params = [{'path': raw_path, 'raw_format': raw_format}
                      for raw_path in raw_paths]
            with Pool(self.n_cores) as p:
                self._logger.log("Reading with {} processes".format(self.n_cores))
                raw_data_async = [p.apply_async(self._read_raw_file, (param,)) for param in params]
                progress = ApplyProgressBar(apply_results=raw_data_async)
                progress.track_progress()

            return raw_data_async

        return action(*args, **kwargs)

    @staticmethod
    def _read_raw_file(param: dict) -> pd.DataFrame:
        raw_datum = pd.read_csv(param['path'], **param['raw_format'])
        raw_datum.set_index(raw_datum.columns[0], inplace=True)
        return raw_datum

    def _merge_raw_data(self, *args, **kwargs):
        @self._logger.log_action('Merging [{}] data'.format('null'))
        def action(raw_data_async):
            raw_data = pd.concat([raw_datum_async.get() for raw_datum_async in raw_data_async])
            return raw_data

        return action(*args, **kwargs)


class SonicRawConverter(RawConverter):

    def prepare_sonic_data(self):
        @self._logger.log_process('Splitting data for EddyPro input')
        def process():
            data_and_range_fractions = self._make_data_fracs(self.raw_data, self._config.data_periods)
            self._split_data_fracs_main(data_and_range_fractions)

        process()

    def _split_data_fracs_main(self, data_and_range_fractions):
        @self._logger.log_action('Splitting data fractions')
        def action():
            with Pool(self.n_cores) as p:
                split_path = self._config.cvt_dir
                os.makedirs(split_path, exist_ok=True)
                results = [p.apply_async(self._split_data_fractions_sub, (*data_and_range_fraction, split_path)) for
                           data_and_range_fraction in data_and_range_fractions]
                print('len:{}'.format(len(results)))
                progress = ApplyProgressBar(apply_results=results)
                progress.track_progress()

        action()

    def _make_data_fracs(self, data: pd.DataFrame, data_range):
        @self._logger.log_action('Making data fractions')
        def action():
            fraction_size, extra = divmod(len(data_range), self.n_cores * 8)
            if extra:
                fraction_size += 1
            data_range_iter = iter(data_range)
            while 1:
                fraction = tuple(islice(data_range_iter, fraction_size))
                if not fraction:
                    return
                start_time = fraction[0]
                end_time = fraction[-1] + data_range.freq
                data_range_fraction = pd.date_range(fraction[0], fraction[-1], freq=data_range.freq)
                try:
                    yield (data[start_time:end_time], data_range_fraction)
                except Exception as e:
                    print(e)

        return action()

    @staticmethod
    def _split_data_fractions_sub(data_fraction: pd.DataFrame, data_range_fraction, split_path: str):
        i = 0
        while i < len(data_range_fraction):
            start_time = data_range_fraction[i]
            end_time = start_time + data_range_fraction.freq
            try:
                data_part = data_fraction[start_time:end_time]
                # convert to "yyyy-mm-dd_HH-MM" for EddyPro input
                part_name = str(start_time.date()) + '_' + str(start_time.time()).replace(':', '-')[:-3]
                file_path = split_path + '\\' + part_name + '.csv'
                data_part.to_csv(file_path, index=False)
            except Exception as e:
                print("%s : %s" % (str(e), start_time))
            i += 1
        return True


class AmmoniaRawConverter(RawConverter):
    def prepare_ammonia_data(self):
        print(">>> Averaging data")
        self.raw_data = self.raw_data.tshift(8, freq='H')  # Time Zone Change
        data_prep = self.raw_data.resample(self._config.data_periods.freq).mean()
        os.makedirs(self._config.cvt_dir, exist_ok=True)
        data_prep.to_csv(self._config.cvt_dir + r'\data_averaged.csv')
        print("### Averaging data completed.")


class FpModelInitiator:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

        self.output_dir = config['fp_dir']
        self.eddy_results_dir = config['eddy_results_dir']

    def initialize_model(self):
        self._write_model_params()
        self._convert_met_data()

    def _write_model_params(self):
        z_m = self.config['measure_height']
        z_0 = self.config['roughness_height']
        x_max = self.config['x_range']
        y_max = self.config['y_range']
        dx = self.config['grid_size']
        station_x = self.config['station_x']
        station_y = self.config['station_y']

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.output_dir + '\\01paras.dat', mode='w') as param_file:
            param_file.write('{:.1f},{:.2f}, `\n'.format(z_m, z_0))
            param_file.write('{:.1f},{:.1f},{:d}, `\n'.format(x_max, y_max, dx))
            param_file.write('100,100,100,100, `\n880e-9, `\n0.145, `\n')
        with open(self.output_dir + '\\monit.pst', mode='w') as station_file:
            station_file.write('{:.3f},{:.3f},1# \n'.format(station_x, station_y))

    def _convert_met_data(self):
        result_path = get_path(target_dir=self.eddy_results_dir,
                               file_init='eddypro_ADV_full_output',
                               file_ext='adv.csv')
        order = ['date',
                 'time',
                 'wind_dir',
                 'wind_speed',
                 'u*',
                 'L',
                 'H',
                 'air_density',
                 'v_var']
        flux_full = pd.read_csv(result_path,
                                skiprows=[0, 2],
                                usecols=order,
                                parse_dates=[[0, 1]],
                                na_values=-9999)
        flux_full.set_index(flux_full.columns[0], inplace=True)
        flux_full.dropna(inplace=True)
        flux_full['key'] = 1
        out_order = ['wind_dir',
                     'wind_speed',
                     'sigma_v',
                     'u*',
                     'L',
                     'H',
                     'air_density',
                     'key']
        flux_full['sigma_v'] = flux_full['v_var'] ** 0.5
        flux_out = flux_full[out_order]
        out_cols = ['wd(deg)',
                    'U(m/s)',
                    'Sgm_v',
                    'u*(m/s)',
                    'L(m)',
                    'H(J/m2)',
                    'rho(kg/m3)',
                    'key(1/0==use ustar & Obu_L /use H_sensible heat)']
        flux_out.columns = out_cols
        flux_out.to_csv(self.output_dir + '\\02metdata.dat',
                        date_format='%y%m%d%H%M',
                        index_label='Datetime',
                        sep='\t',
                        float_format='%.3f')


class EPProxy:
    def __init__(self):
        pass

    def modify_and_run(self):
        self._modify_metadata()
        self._modify_ep_project()
        self._run_ep()

    def _modify_ep_project(self):
        pass

    def _modify_metadata(self):
        pass

    def _run_ep(self):
        pass

class FluxEstimator(BaseProcessModule):

    def calc_emission(self):
        DATA_PATH = r'd:\Desktop\present_work\01_ammonia\02_prelim\03_Summer2018\02_source'
        FC_SUM = DATA_PATH + r'\fc_sum.csv'
        C_N = DATA_PATH + r'\c_n.csv'
        C_S = DATA_PATH + r'\c_s.csv'
        SUM_UP = DATA_PATH + r'\sum_up.csv'
        dateparse = lambda dates: pd.datetime.strptime(dates[0:10], '%y%m%d%H%M')
        order_f = [' Datetm', ' Site_no', ' Fcsum(s/m)', ' Ratio(%)']  # todo
        order_c = ['DATE_TIME', 'NH3_Raw']
        fc_sum = pd.read_csv(FC_SUM, usecols=order_f, na_values=-9999, parse_dates=[0], date_parser=dateparse)
        fc_sum.set_index(fc_sum.columns[0], inplace=True)
        fc_n = fc_sum[fc_sum[' Site_no'] == '#1']
        fc_s = fc_sum[fc_sum[' Site_no'] == '#2']
        fc_n.drop(columns=[' Site_no'], inplace=True)
        fc_s.drop(columns=[' Site_no'], inplace=True)
        fc_n.columns = ['Fc_n', 'R_n']
        fc_s.columns = ['Fc_s', 'R_s']
        # c_n = read_csv(FP_SUM, skiprows=[0, 2], usecols=order, parse_dates=[[0, 1]], na_values=-9999) #todo
        c_n = read_csv(C_N, usecols=order_c, parse_dates=[0], na_values=-9999)
        c_n.set_index(c_n.columns[0], inplace=True)
        c_n.columns = ['c_n']
        c_s = read_csv(C_S, usecols=order_c, parse_dates=[0], na_values=-9999)
        c_s.set_index(c_s.columns[0], inplace=True)
        c_s.columns = ['c_s']
        c_all = pd.merge(c_n, c_s, left_index=True, right_index=True, how='outer')
        fc_all = pd.merge(fc_n, fc_s, left_index=True, right_index=True, how='outer')
        sumup = pd.merge(fc_all, c_all, left_index=True, right_index=True, how='outer')
        sumup.eval('Qn = (c_n -c_s)/Fc_n', inplace=True)
        sumup.eval('Qs = (c_s -c_n)/Fc_s', inplace=True)
        sumup.replace([np.inf, -np.inf], np.nan, inplace=True)
        sumup.to_csv(SUM_UP)
        # print(fc_n)
        # print(c_all)
        # print(c_s)
        # print(c_n)
        print(sumup)


