from core.frame import Project
from multiprocessing import freeze_support
if __name__ == '__main__':
    freeze_support()
    test_proj = Project()
    test_proj.load_config(config_path='test_conf.json')
    test_proj.prepare_raw_data()