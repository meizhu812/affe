from core.data import Project
from multiprocessing import freeze_support
if __name__ == '__main__':
    freeze_support()
    test_project = Project(log_separated=True)
    test_project.load_config('new.json')
    test_project.prepare_raw_data()

