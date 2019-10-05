import json
import os
import sys
from itertools import islice
from multiprocessing import Pool

import pandas as pd

from core.base import BaseModule
from core.file import get_paths
from util.logger import logger
from util.pgbar import ProgressBar


class RawConverter(BaseModule):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._p_cores = None
        self._io_threads = None

        self._raw_dir = None
        self._cvt_dir = None
        self._raw_fmt_code = None
        self._raw_init = None
        self._raw_ext = None

        self._parse_config()

        self.raw_data = None
        self.temp_data = None

    def _parse_config(self):
        prj_conf = self._config['Project']
        self._p_cores = int(prj_conf['CPU_Cores'])
        self._io_threads = self._p_cores * 2  # seems reasonable
        self.data_periods = pd.date_range(prj_conf['Data_Periods_Start'],
                                          prj_conf['Data_Periods_End'],
                                          freq=prj_conf['Data_Averaging_Interval'])

    @logger.log_process('Loading Raw Data', timed=False)
    def load_raw_data(self):
        try:
            with open('formats.json') as fmt:
                raw_fmt = json.load(fmt)[self._raw_fmt_code]
                print(raw_fmt)
        except Exception as e:
            print(e)
            sys.exit(1)

        raw_paths = self._get_raw_paths(raw_dir=self._raw_dir, file_init=self._raw_init, file_ext=self._raw_ext)
        raw_data_async = self._get_raw_data(raw_paths, raw_fmt)
        print(len(raw_data_async))
        self.raw_data = self._merge_raw_data(raw_data_async)

    @logger.log_action('Getting raw data files', timed=False)
    def _get_raw_paths(self, *, raw_dir: str, file_init: str, file_ext: str):
        logger.log("Listing files in folder: [{}]".format(raw_dir))
        logger.log("[INIT]:'{}'\t".format(file_init) + "[EXT]:'{}'".format(file_ext))

        raw_paths = get_paths(target_dir=raw_dir, file_init=file_init, file_ext=file_ext)

        for raw_path in raw_paths[:3]:  # print heads
            logger.log(raw_path)
        logger.log(6 * '...')
        for raw_path in raw_paths[-3:]:  # print tails
            logger.log(raw_path)

        logger.log('[ {} ] files found.'.format(len(raw_paths)))
        logger.log('Check sequence of raw data files, press Enter to continue...')
        input()
        return raw_paths

    @logger.log_action('Getting Raw data')
    def _get_raw_data(self, raw_paths: list, raw_format: dict):
        with Pool(self._io_threads) as p:
            self._logger.log("Reading with {} processes".format(self._io_threads))
            pgb = ProgressBar(target=len(raw_paths))
            raw_data_async = [p.apply_async(self._get_raw_data_sub, (raw_path, raw_format), callback=pgb.update)
                              for raw_path in raw_paths]
            p.close()
            p.join()

            return raw_data_async

    @staticmethod
    def _get_raw_data_sub(raw_path, raw_format):
        raw_datum = pd.read_csv(raw_path, **raw_format)
        raw_datum.set_index(raw_datum.columns[0], inplace=True)
        return raw_datum

    def _merge_raw_data(self, raw_data_async):
        @self._logger.log_action('Merging data')
        def action():
            raw_data = pd.concat([raw_datum_async.get() for raw_datum_async in raw_data_async])
            return raw_data

        return action()


class SonicRawConverter(RawConverter):

    def _parse_config(self):
        super()._parse_config()

        srp_conf = self._config['Sonic']
        self._raw_dir = srp_conf['Raw_Data_Directory']
        self._cvt_dir = srp_conf['Converted_Data_Output_Directory']
        self._raw_fmt_code = srp_conf['Raw_Data_Format_Code']
        self._raw_init = srp_conf['Raw_Data_Initial']
        self._raw_ext = srp_conf['Raw_Data_Extension']

    @logger.log_process('Splitting data for EP input')
    def convert_sonic_data(self):
        data_and_period_fractions = self._make_fracs(self.raw_data, self.data_periods)
        self._split_fracs(data_and_period_fractions)

    @logger.log_action('Splitting data fractions')
    def _split_fracs(self, data_and_period_fracs):
        split_pool = Pool(self._io_threads)
        pgb = ProgressBar(target=len(data_and_period_fracs))
        split_path = self._cvt_dir
        os.makedirs(split_path, exist_ok=True)
        [split_pool.apply_async(self._split_fracs_sub, (*data_and_range_frac, split_path), callback=pgb.update) for
         data_and_range_frac in data_and_period_fracs]
        split_pool.close()
        split_pool.join()

    @logger.log_action('Making moduless fractions')
    def _make_fracs(self, data: pd.DataFrame, data_range):
        # the inner_action return a generator which needs to be converted into a list
        def inner_action():
            fraction_size, extra = divmod(len(data_range), self._io_threads * 8)
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
                    print(e, start_time)

        return list(inner_action())

    @staticmethod
    def _split_fracs_sub(data_fraction: pd.DataFrame, data_range_fraction, split_path: str):
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
    def _parse_config(self):
        super()._parse_config()

        arp_conf = self._config['Ammonia']
        self._raw_dir = arp_conf['Raw_Data_Directory']
        self._cvt_dir = arp_conf['Converted_Data_Output_Directory']
        self._raw_fmt_code = arp_conf['Raw_Data_Format_Code']
        self._raw_init = arp_conf['Raw_Data_Initial']
        self._raw_ext = arp_conf['Raw_Data_Extension']

    def prepare_ammonia_data(self):
        print(">>> Averaging data")
        self.raw_data = self.raw_data.tshift(8, freq='H')  # Time Zone Change
        data_prep = self.raw_data.resample(self.data_periods.freq).mean()
        os.makedirs(self._cvt_dir, exist_ok=True)
        data_prep.to_csv(self._cvt_dir + r'\data_averaged.csv')
        print("### Averaging data completed.")
