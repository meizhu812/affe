from unittest import TestCase
from util.logger import ConsoleLogger
from time import sleep

'''
class TestTimer(TestCase):
    def setUp(self) -> None:
        self.timer = Timer(start_now=False)

    def tearDown(self) -> None:
        del self.timer

    def test_timer(self):
        from time import sleep
        print('\ntest_timer')
        self.timer.reset(start_now=True)
        sleep(1)
        print(self.timer.lap_time, self.timer.split_time)
        sleep(2)
        print(self.timer.lap_time, self.timer.split_time)
        sleep(3)
        print(self.timer.lap_time, self.timer.split_time)
        self.assertEqual(self.timer._on, True)
        self.timer.stop()
        self.assertEqual(self.timer._on, False)
        self.assertEqual(self.timer.error, False)
        sleep(0.1)

    def test_duplicate_start(self):
        print('\ntest_duplicate_start')
        self.timer.reset(start_now=True)
        self.timer.start()
        self.assertEqual(self.timer.error, True)

    def test_duplicate_stop(self):
        print('\ntest_duplicate_stop')
        self.timer.reset(start_now=True)
        self.timer.stop()
        self.timer.stop()
        self.assertEqual(self.timer.error, True)
'''


class TestLogger(TestCase):
    def setUp(self) -> None:
        self.logger = ConsoleLogger()

    def _manual_process(self):
        @self.logger.log_process('Manual Process', timed=False)
        def process():
            input('Press enter to continue...')

        process()

    def _timed_process(self):
        @self.logger.log_process('Timed Process')
        def process():
            self.logger._process_msg('[Running dummy process for 2 seconds.]')
            sleep(2)

        process()

    def _compound_process(self):
        @self.logger.log_process('Compound Process')
        def process():
            self._simple_action1()
            self._simple_action2()

        process()

    def _simple_action1(self):
        @self.logger.log_action('Simple Action I')
        def action():
            self.logger._action_msg('[Running dummy action for 1 second.]')
            sleep(2)

        action()

    def _simple_action2(self):
        @self.logger.log_action('Simple Action II')
        def action():
            self.logger._action_msg('[Running dummy action for 1 second.]')
            sleep(2)

        action()

    def test_logger(self):
        self._manual_process()
        self._timed_process()
        self._compound_process()
        sleep(0.5)
