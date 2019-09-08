


class Project:
    def __init__(self):
        self.configs_handler = ConfigsHandler()
        self.configs_handler.load_configs()
        # Dispatch configs of project, sonic_raw_prep, ammonia_raw_prep and fp_model_init
        self.prj_conf, self.srp_conf, self.arp_conf, self.fmi_conf = self.configs_handler.dispatch_configs()

    def convert_raw_data(self):
        pass

    def output_statistics(self):
        pass

    def calculate_fp(self):
        pass

    def output_tables(self):
        pass

    def output_plots(self):
        pass


class Process:
    pass
