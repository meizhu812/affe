from unittest import TestCase
from util import ProgressBar
from multiprocessing import Pool, freeze_support
from time import sleep


def func( x):
    sleep(1)
    return 2 / (2 ** x)

class TestApplyProgressBar(TestCase):

    def setUp(self) -> None:
        self.test_input = list(range(100))




    def test_track_progress(self):
        freeze_support()
        with Pool(8) as p:
            test_results = [p.apply_async(func, (x,)) for x in self.test_input]
            pgb = ProgressBar(apply_results=test_results)
            pgb.track_progress()
            print(sum([test_result.get() for test_result in test_results]))
