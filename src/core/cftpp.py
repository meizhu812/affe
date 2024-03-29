import os
import shutil
import subprocess

import pandas as pd

from core.file import get_path, get_paths
from core.modules import FpGrdGenerator
from util.pgbar import ProgressBar


class FpGrdGeneratorClassic(FpGrdGenerator):

    def _parse_config(self):
        self.n_cores = int(self._config['Project']['CPU_Cores'])

        fpgc_conf = self._config['Footprint']
        self._epr_dir = fpgc_conf['Eddy_Pro_Results_Directory']
        self._fpm_path = fpgc_conf['Footprint_Model_Path']
        self._fpout_dir = fpgc_conf['Footprint_Data_Output_Directory']
        self._out_dirs = [self._fpout_dir + '\\proc{}'.format(n) for n in range(self.n_cores)]
        self._params = list(map(float, fpgc_conf['LegacyParameters'].split(',')))  # convert param string into floats

    def _initialize_fp_model(self):
        @self._logger.log_action('Initializing Footprint Model Parameters')
        def action():
            self._write_model_params()
            self._convert_met_data()

        action()

    def _run_fp_model(self):
        @self._logger.log_action('Running Footprint Model in parallel')
        def action():
            self._run_fp_model_parallel()
            self._rearrange_and_cleanup()

        action()

    def _write_model_params(self):
        for n in range(self.n_cores):
            os.makedirs(self._out_dirs[n], exist_ok=True)
            with open(self._out_dirs[n] + '\\01paras.dat', mode='w') as param_file:
                param_file.write('{:.1f},{:.2f}, `\n'.format(self._params[0], self._params[1]))  # z_m, z_0
                param_file.write('{:.1f},{:.1f},{:.1f}, `\n'.format(*self._params[2:5]))  # x_max, y_max, dx
                param_file.write('100,100,100,100, `\n880e-9, `\n0.145, `\n')  # TODO may alter after checking
            with open(self._out_dirs[n] + '\\monit.pst', mode='w') as station_file:
                station_file.write('{:.3f},{:.3f},1# \n'.format(*self._params[5:7]))  # x_loc, y_loc

    def _convert_met_data(self):
        result_path = get_path(target_dir=self._epr_dir,
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
        flux_out.to_csv(self._fpout_dir + '\\02metdata.dat', date_format='%y%m%d%H%M',
                        index_label='Datetime',
                        sep='\t',
                        float_format='%.3f')
        for n in range(self.n_cores):
            nth_out = flux_out.iloc[n * seg: (n + 1) * seg]
            nth_out.to_csv(self._out_dirs[n] + '\\02metdata.dat',
                           date_format='%y%m%d%H%M',
                           index_label='Datetime',
                           sep='\t',
                           float_format='%.3f')

    def _run_fp_model_parallel(self):

        fme_paths = [os.path.join(self._out_dirs[n], 'cftp{}.exe'.format(n)) for n in range(self.n_cores)]
        processes = []
        for fme_path in fme_paths:
            shutil.copyfile(self._fpm_path, fme_path)
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

    def _rearrange_and_cleanup(self):
        @self._logger.log_action('Rearranging Footprint Grid Files and Cleaning up')
        def action():
            for out_dir in self._out_dirs:  # go though all sub-folders
                grd_files = get_paths(target_dir=out_dir, file_ext='.grd')
                for grd_file in grd_files:  # move all .grd files
                    file_dir, file_name = os.path.split(grd_file)
                    shutil.move(grd_file, os.path.join(self._fpout_dir, file_name))
                shutil.rmtree(out_dir)  # remove all sub-folders and containing temp files

        action()
