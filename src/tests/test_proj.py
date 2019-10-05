from multiprocessing import freeze_support

from core.project import Project

if __name__ == '__main__':
    freeze_support()
    test_proj = Project()
    test_proj.init(config_path='test_conf.ini')
    test_proj.set_log_path('logs.log')

    # test_proj.prepare_sonic_data()
    # test_proj.prepare_ammonia_data()
    test_proj.generate_turb_stats()
    # test_proj.generate_fp_grds()
    # test_proj.plot()
