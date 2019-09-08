from core.data import Project
from multiprocessing import freeze_support
if __name__ == '__main__':
    freeze_support()
    test_project = Project(log_separated=True)
    test_project.load_config('2018SN.json')
    #test_project.prepare_raw_data()
    test_project.initialize_fp_model()

