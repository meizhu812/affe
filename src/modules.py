import configparser
import datetime
import os
import shutil
import subprocess
from collections import namedtuple
from itertools import islice
from multiprocessing import Pool

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt, dates as dates

from file import get_paths, get_path
from util import ProgressBar, Logger


class BaseDataModule:
    def __init__(self, prj_config: dict, mod_config: dict, logger: Logger):
        self.n_cores = prj_config['physical_cores_available']
        self._logger = logger
        self._mod_config = mod_config
        self._parse_config()

    def _parse_config(self):
        raise NotImplementedError


class RawConverter(BaseDataModule):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.raw_data = None
        self.temp_data = None

    def _parse_config(self):
        # the purpose of using namedtuple is to use '.' operator to access specific config item in a more intuitive way.
        rc_config = namedtuple('rc_config', ['raw_dir',
                                             'cvt_dir',
                                             'raw_format',
                                             'raw_pattern',
                                             'data_periods'])
        self.config = rc_config(self._mod_config['raw_files_directory'],
                                self._mod_config['converted_files_directory'],
                                self._mod_config['raw_data_format'],
                                self._mod_config['raw_filenames_pattern'],
                                pd.date_range(**self._mod_config['data_periods_parameters']))

    def load_raw_data(self):
        @self._logger.log_process('Loading Raw Data', timed=False)
        def process():
            raw_paths = self._get_raw_paths(raw_dir=self.config.raw_dir, **self.config.raw_pattern)
            raw_data_async = self._get_raw_data(raw_paths, self.config.raw_format)
            print(len(raw_data_async))
            self.raw_data = self._merge_raw_data(raw_data_async)

        process()

    def _get_raw_paths(self, *, raw_dir: str, file_init: str, file_ext: str):
        @self._logger.log_action('Getting raw moduless files', timed=False)
        def action():
            self._logger.log("Listing files in folder: [{}]".format(raw_dir))
            self._logger.log("[INIT]:'{}'\t".format(file_init) + "[EXT]:'{}'".format(file_ext))

            raw_paths = get_paths(target_dir=raw_dir, file_init=file_init, file_ext=file_ext)

            for raw_path in raw_paths[:3]:  # print heads
                self._logger.log(raw_path)
            self._logger.log(6 * '...')
            for raw_path in raw_paths[-3:]:  # print tails
                self._logger.log(raw_path)

            self._logger.log('[ {} ] files found.'.format(len(raw_paths)))
            self._logger.log('Check sequence of raw moduless files, press Enter to continue...')
            input()
            return raw_paths

        return action()

    def _get_raw_data(self, *args, **kwargs):
        @self._logger.log_action('Getting [{}] moduless'.format('Raw'))
        def action(raw_paths: list, raw_format: dict):
            with Pool(self.n_cores) as p:
                self._logger.log("Reading with {} processes".format(self.n_cores))
                pgb = ProgressBar(target=len(raw_paths))
                raw_data_async = [p.apply_async(self._get_raw_data_sub, (raw_path, raw_format), callback=pgb.update)
                                  for raw_path in raw_paths]
                p.close()
                p.join()

                return raw_data_async

        return action(*args, **kwargs)

    @staticmethod
    def _get_raw_data_sub(raw_path, raw_format):
        raw_datum = pd.read_csv(raw_path, **raw_format)  # raw_path and **raw_format
        raw_datum.set_index(raw_datum.columns[0], inplace=True)
        return raw_datum

    def _merge_raw_data(self, raw_data_async):
        @self._logger.log_action('Merging [{}] moduless'.format('null'))
        def action():
            raw_data = pd.concat([raw_datum_async.get() for raw_datum_async in raw_data_async])
            return raw_data

        return action()


class SonicRawConverter(RawConverter):

    def convert_sonic_data(self):
        @self._logger.log_process('Splitting moduless for EP input')
        def process():
            data_and_period_fractions = self._make_fracs(self.raw_data, self.config.data_periods)
            self._split_fracs(data_and_period_fractions)

        process()

    def _split_fracs(self, data_and_period_fracs):
        @self._logger.log_action('Splitting moduless fractions')
        def action():
            split_pool = Pool()
            pgb = ProgressBar(target=len(data_and_period_fracs))
            split_path = self.config.cvt_dir
            os.makedirs(split_path, exist_ok=True)
            [split_pool.apply_async(self._split_fracs_sub, (*data_and_range_frac, split_path), callback=pgb.update) for
             data_and_range_frac in data_and_period_fracs]
            split_pool.close()
            split_pool.join()

        action()

    def _make_fracs(self, data: pd.DataFrame, data_range):
        @self._logger.log_action('Making moduless fractions')
        # the inner_action return a generator which needs to be converted into a list
        def action():
            def inner_action():
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
                        print(e, start_time)

            return list(inner_action())

        return action()

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
    def prepare_ammonia_data(self):
        print(">>> Averaging moduless")
        self.raw_data = self.raw_data.tshift(8, freq='H')  # Time Zone Change
        data_prep = self.raw_data.resample(self.config.data_periods.freq).mean()
        os.makedirs(self.config.cvt_dir, exist_ok=True)
        data_prep.to_csv(self.config.cvt_dir + r'\data_averaged.csv')
        print("### Averaging moduless completed.")


class EPProxy(BaseDataModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.total_files = None

    def _parse_config(self):
        epp_config = namedtuple('epp_config',
                                ['cli_path',
                                 'prj_path'])
        self.config = epp_config(self._mod_config['eddypro_cli_path'],
                                 self._mod_config['eddypro_project_path'])

    def modify_and_run(self):
        @self._logger.log_process('Calculating Turbulence Statistics')
        def process():
            self._modify_ep_project()
            self._run_ep()

        process()

    def _modify_ep_project(self):
        @self._logger.log_action('Creating metadata and project configs', timed=False)
        def action():
            ep_config = configparser.ConfigParser()
            ep_config.read(self.config.prj_path)
            self.total_files = len(os.listdir(ep_config.get('RawProcess_General', 'data_path')))

        action()

    def _run_ep(self):
        @self._logger.log_action('Running EddyPro in background')
        def action():
            process = subprocess.Popen([self.config.cli_path, self.config.prj_path], shell=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ep_pgb = ProgressBar(target=self.total_files)
            rp_ended = False

            while True:  # the program does not quit and return a code, instead it outputs an err/warning and hangs
                output = process.stdout.readline().decode('utf8').strip()
                if output.startswith('From:'):
                    ep_pgb.update()
                elif output.startswith('Raw moduless processing terminated.'):
                    rp_ended = True
                elif output.startswith('Done.') and rp_ended:
                    process.terminate()  # manually kill the subprocess
                    break

        action()


class FpGrdGenerator(BaseDataModule):
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
            self._run_fp_model()

        process()

    def _initialize_fp_model(self):
        raise NotImplementedError

    def _run_fp_model(self):
        raise NotImplementedError


class FpGrdGeneratorClassic(FpGrdGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.out_dirs = [self.config.fpout_dir + '\\proc{}'.format(n) for n in range(self.n_cores)]

    def _initialize_fp_model(self):
        @self._logger.log_action('Initializing Footprint Model Parameters')
        def action():
            self._write_model_params()
            self._convert_met_data()
            self._run_fp_model()
            self._rearrange_and_cleanup()

        action()

    def _write_model_params(self):
        for n in range(self.n_cores):
            os.makedirs(self.out_dirs[n], exist_ok=True)
            with open(self.out_dirs[n] + '\\01paras.dat', mode='w') as param_file:
                param_file.write('{:.1f},{:.2f}, `\n'.format(self.config.z_m, self.config.z_0))
                param_file.write('{:.1f},{:.1f},{:d}, `\n'.format(self.config.x_max, self.config.y_max, self.config.dx))
                param_file.write('100,100,100,100, `\n880e-9, `\n0.145, `\n')  # TODO may alter after checking
            with open(self.out_dirs[n] + '\\monit.pst', mode='w') as station_file:
                station_file.write('{:.3f},{:.3f},1# \n'.format(self.config.loc_x, self.config.loc_y))

    def _convert_met_data(self):
        result_path = get_path(target_dir=self.config.epr_dir,
                               file_init='eddypro_ADV_essentials',
                               file_ext='adv.csv')
        order = ['date',
                 'time',
                 'wind_dir',
                 'wind_speed',
                 'u*',
                 'L',
                 'H',
                 'rho_air',
                 'var(v)']
        flux_full = pd.read_csv(result_path,
                                usecols=order,
                                parse_dates=[[0, 1]],
                                na_values=-9999)
        flux_full.set_index(flux_full.columns[0], inplace=True)
        flux_full.dropna(inplace=True)
        flux_full['key'] = 1
        out_order = ['wind_dir', 'wind_speed', 'sigma_v', 'u*', 'L', 'H', 'rho_air',
                     'key']
        flux_full['sigma_v'] = flux_full['var(v)'] ** 0.5
        flux_out = flux_full[out_order]
        out_cols = ['wd(deg)', 'U(m/s)', 'Sgm_v', 'u*(m/s)', 'L(m)', 'H(J/m2)', 'rho(kg/m3)',
                    'key(1/0==use ustar & Obu_L /use H_sensible heat)']
        flux_out.columns = out_cols
        self.total = len(flux_out)
        seg = self.total // self.n_cores + 1
        for n in range(self.n_cores):
            nth_out = flux_out.iloc[n * seg: (n + 1) * seg]
            nth_out.to_csv(self.out_dirs[n] + '\\02metdata.dat',
                           date_format='%y%m%d%H%M',
                           index_label='Datetime',
                           sep='\t',
                           float_format='%.3f')

    def _run_fp_model(self):
        @self._logger.log_action('Running Footprint Model in parallel')
        def action():
            fme_paths = [os.path.join(self.out_dirs[n], 'cftp{}.exe'.format(n)) for n in range(self.n_cores)]
            processes = []
            for fme_path in fme_paths:
                shutil.copyfile(self.config.cli_path, fme_path)
                processes.append(subprocess.Popen(fme_path, cwd=os.path.split(fme_path)[0], stdout=subprocess.PIPE,
                                                  stderr=subprocess.PIPE))
            fme_pgb = ProgressBar(target=self.total)
            while processes:
                for n, process in enumerate(processes):
                    output = process.stdout.readline().decode('utf8').strip()
                    if output.startswith('ouput file'):
                        fme_pgb.update()
                    elif output.startswith('ok, please'):
                        process.terminate()
                        processes.pop(n)

        action()

    def _rearrange_and_cleanup(self):
        @self._logger.log_action('Rearranging Footprint Grid Files and Cleaning up')
        def action():
            for out_dir in self.out_dirs:  # go though all sub-folders
                grd_files = get_paths(target_dir=out_dir, file_ext='.grd')
                for grd_file in grd_files:  # move all .grd files
                    file_dir, file_name = os.path.split(grd_file)
                    shutil.copy(grd_file, os.path.join(self.config.fpout_dir, file_name))
                shutil.rmtree(out_dir)  # remove all sub-folders and containing temp files

        action()


class FpGrdProcessor(BaseDataModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _parse_config(self):
        pass

    @staticmethod
    def _get_grd_data(grd_path):
        with open(grd_path, 'r') as f:
            heads = []  # first 5 lines of grd file
            for n in range(5):
                heads.append(f.readline())
            nx, ny = map(int, heads[1].split())
            data_fracs = []
            while True:
                line = f.readline()
                if not line:  # end of file
                    break
                data_fracs.append(np.fromstring(line, sep=' ', dtype='f4'))
        return np.concatenate(data_fracs).reshape(nx, ny)

    @staticmethod
    def _plot_grd(grd_data, grd_path):
        plt.contourf(grd_data)
        plt.savefig(os.path.splitext(grd_path)[0] + '.png', dpi=300)


class Plotter(BaseDataModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._load_data()

    def _parse_config(self):
        tsp_config = namedtuple('tsp_config', ['stat_dir',
                                               'amd_path',
                                               'plot_path',
                                               'plot_settings'])
        self.config = tsp_config(self._mod_config['meteorology_statistics_directory'],
                                 self._mod_config['ammonia_data_path'],
                                 self._mod_config['plot_path'],
                                 self._mod_config['plot_settings'])

    def _load_data(self):
        result_path = get_path(target_dir=self.config.stat_dir,
                               file_init='eddypro_ADV_essentials',
                               file_ext='adv.csv')
        useful_cols = ['date',
                       'time',
                       'wind_dir',
                       'wind_speed',
                       'H',
                       't_air',
                       'rh_air']
        met_data = pd.read_csv(result_path,
                               usecols=useful_cols,
                               parse_dates=[[0, 1]],
                               na_values=-9999)
        met_data.set_index(met_data.columns[0], inplace=True)
        am_data = pd.read_csv(self.config.amd_path, parse_dates=[0])
        am_data.set_index(am_data.columns[0], inplace=True)
        self.data = am_data.join(met_data)
        self.data['T'] = self.data['t_air'] - 273.15
        self.data.drop('t_air', axis=1)

    def plot_windrose(self):
        pass

    def plot_hourly_box(self):
        pass

    def plot_summary(self):
        fig_size = (30, 20)
        multi_plot = plt.figure(figsize=fig_size, dpi=300)
        plot_order = ['wind_speed', 'wind_dir', 'T', 'rh_air', 'H']
        for sub_name in plot_order:
            sub_plot = multi_plot.add_subplot(self._get_pos(sub_name, plot_order),
                                              xlim=[self.data.index[0].date(), self.data.index[-1].date()],
                                              ylim=self.config.plot_settings[sub_name]['ylim'])
            plt.plot(self.data[sub_name], self.config.plot_settings[sub_name]['style'],
                     **self.config.plot_settings[sub_name]['params'])

            sub_plot.tick_params(axis='both', length=10, which='major', direction='in', labelsize=14)

            sub_plot.xaxis.set_major_formatter(dates.DateFormatter('%m/%d'))
            sub_plot.xaxis.set_major_locator(dates.DayLocator())
            sub_plot.set_xlabel('Date', fontsize=18)

            sub_plot.set_ylabel(self.config.plot_settings[sub_name]['label'], fontsize=18)
            sub_plot.yaxis.set_major_locator(plt.FixedLocator(self.config.plot_settings[sub_name]['y_ticks']))

        # multi_plot.tight_layout()
        os.makedirs(self.config.plot_path, exist_ok=True)
        plt.savefig(self.config.plot_path + '\\all_ADV.png')
        plt.close(multi_plot)

    def plot_daily_ts(self):
        data_range = pd.date_range(self.data.index[0].date(), self.data.index[-1].date() + datetime.timedelta(days=1))
        daily_data = []
        for n in range(len(data_range) - 1):
            daily_data.append(self.data[data_range[n]:data_range[n + 1]])
        for data in daily_data:
            print(data.describe())
            try:
                self._plot_daily_ts(data)
            except Exception as e:
                print('err {}'.format(e))

    @staticmethod
    def _get_pos(sub: str, order: list):
        return int("%s1%s" % (len(order), order.index(sub) + 1))  # e.g.312 means 2nd row of 3 in single column

    def _plot_daily_ts(self, data):
        fig_size = (14, 20)
        multi_plot = plt.figure(figsize=fig_size, dpi=300)
        plot_order = ['wind_speed', 'wind_dir', 't_air', 'rh_air', 'H']
        for sub_name in plot_order:
            sub_plot = multi_plot.add_subplot(self._get_pos(sub_name, plot_order),
                                              xlim=[data.index[0].date(), data.index[-1].date()],
                                              ylim=self.config.plot_settings[sub_name]['ylim'])
            plt.plot(data[sub_name], self.config.plot_settings[sub_name]['style'],
                     **self.config.plot_settings[sub_name]['params'])

            sub_plot.tick_params(axis='both', length=10, which='major', direction='in', labelsize=14)
            sub_plot.tick_params(axis='both', length=5, which='minor', direction='in', labelsize=14)

            sub_plot.xaxis.set_major_formatter(dates.DateFormatter('%m/%d'))
            sub_plot.xaxis.set_major_locator(dates.DayLocator())
            sub_plot.xaxis.set_minor_locator(dates.HourLocator())
            sub_plot.set_xlabel('Date', fontsize=18)

            sub_plot.set_ylabel(self.config.plot_settings[sub_name]['label'], fontsize=18)
            sub_plot.yaxis.set_major_locator(plt.FixedLocator(self.config.plot_settings[sub_name]['y_ticks']))

        # multi_plot.tight_layout()
        os.makedirs(self.config.plot_path, exist_ok=True)
        plt.savefig(self.config.plot_path + '\\' + str(data.index[0].date()) + 'ADV.png')
        plt.close(multi_plot)
