from core.util import Logger





class RawPreparer:

    def __init__(self):
        self.p_threads = self.io_threads = None  # Number of threads for processing and I/O

        self.periods = None  # TODO

        self.raw_dir = self.temp_dir= self.out_dir =None  # TODO

        self.raw_pattern = None # TODO
        self.raw_format = None # TODO


    def load_raw_data(self):
        pass
    def assemble_raw_data(self):
        pass
    def _load_raw_files(self):
        pass
    def _merge_raw_data(self):
        pass

class TurbulenceRawPreparer(RawPreparer):
    def __init__(self):
        super().__init__()
        self.freq = None # TODO


class AmmoniaRawPreparer(RawPreparer):
    def __init__(self):
        super().__init__()
        pass



class Project:
    def __init__(self):
        self.logger = Logger()
        self.conf_hand = ConfigsHandler()
        self.turb_rp = TurbulenceRawPreparer()
        self.ammo_rp = AmmoniaRawPreparer()


    def load_configs(self):
        @self.logger.log_process('Loading Configs', timed=False)
        def process():
            pass

    def set_data_source(self):
        @self.logger.log_process('Setting Data Source for Processing')
        def process():
            pass
    def _set_turb_data_source(self):
        @self.logger.log_action('Setting Turbulence Data Source')
        def action():
            pass

    def _set_ammo_data_source(self):
        @self.logger.log_action('Setting Ammonia Data Source')
        def action():
            pass

    def prepare_turb_data(self):
        @self.logger.log_process('Processing Turbulence Data')
        def process():
            pass

    def prepare_ammo_data(self):
        @self.logger.log_process('Processing Ammonia Data')
        def process():
            pass

    def get_turb_stats(self):
        pass

    def generate_fp(self):
        pass

    def calc_emmision(self):
        pass

    def output_data_sheets(self):
        pass

    def output_plots(self):
        pass
