import configparser
import os
import subprocess

from core.base import BaseModule
from util.logger import logger
from util.pgbar import ProgressBar


class EPProxy(BaseModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.total_files = None

    def _parse_config(self):
        epp_conf = self._config['Eddy_Pro']
        self._bin_dir = epp_conf['Eddy_Pro_Binaries_Directory']
        self._epc_path = epp_conf['Eddy_Pro_Configuration_Path']
        self._keep_logs = bool(epp_conf['Keep_Eddy_Pro_Logs'])

    @logger.log_process('Calculating Turbulence Statistics')
    def modify_and_run(self):
        self._modify_ep_project()
        self._run_ep()

    @logger.log_action('Creating metadata and project configs', timed=False)
    def _modify_ep_project(self):
        ep_config = configparser.ConfigParser()
        ep_config.read(self._epc_path)
        self.total_files = len(os.listdir(ep_config.get('RawProcess_General', 'data_path')))

    @logger.log_action('Running EddyPro in background')
    def _run_ep(self):
        p_rp = subprocess.Popen([os.path.join(self._bin_dir, 'eddypro_rp.exe'), self._epc_path], shell=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ep_pgb = ProgressBar(target=self.total_files)
        while True:  # the program does not quit and return a code, instead it outputs an err/warning and hangs
            output = p_rp.stdout.readline().decode('utf8').strip()
            if output.startswith('Re-calculating'):  # indicates valid time period
                ep_pgb.update()
            elif output.startswith('Note'):
                p_rp.terminate()  # manually kill the subprocess
                break
        print('rp ended, begin fcc')
        p_fcc = subprocess.Popen([os.path.join(self._bin_dir, 'eddypro_fcc.exe'), self._epc_path], shell=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        while True:  # the program does not quit and return a code, instead it outputs an err/warning and hangs
            output = p_fcc.stdout.readline().decode('utf8').strip()
            if output.startswith('Note'):
                p_fcc.terminate()  # manually kill the subprocess
                break
        print('fcc ended')
