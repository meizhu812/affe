from core.frame import Project
from multiprocessing import freeze_support
if __name__ == '__main__':
    freeze_support()
    test_proj = Project()
    test_proj.logger.set_log_path('logs.log')
    test_proj.load_configs(config_path='test_conf.json')
    #test_proj.prepare_raw_data()
    # test_proj.generate_turb_stats()
    test_proj.generate_fp_grds()

