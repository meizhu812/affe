from time import time

from util.consle import console


class ProgressBar:
    def __init__(self, target, interval=5):
        self._major_percentage = 0
        self._progress = 0
        self._target = target
        self._interval = interval
        self._t_last_refresh = time()
        self.start_time = time()
        console.output('[--------------------]......starting...', end='')

    def update(self, result=None):
        self._update_progress()
        if self._refresh_ready:
            self._update_output()
            console.cl()
            console.output(self.current_output, end='')

    def _update_progress(self):
        self._progress += 1

    def _update_output(self):
        self.current_output = self._bar_output() + self._percentage_output() + self._eta_output()

    def _bar_output(self):
        n_blocks = int(self.percentage / 5)  # _major_percentage is int
        return '[{}{}]'.format(n_blocks * '+', (20 - n_blocks) * '-')  # e.g. '[++++++++++----------]'

    def _percentage_output(self):
        return '%3i%%' % self.percentage

    def _eta_output(self):
        if self.percentage == 100:
            return '...finished!\n'
        elif self.percentage >= 90:
            return '...almost done...'
        elif self.percentage >= 25:  # eta becomes stable
            return '...%i seconds remaining...' % self.eta
        else:
            return '...please wait...'

    @property
    def percentage(self):
        return int(self._progress / self._target * 100)

    @property
    def _refresh_ready(self):
        if self._progress == self._target:
            return True
        if time() - self._t_last_refresh >= self._interval:
            self._t_last_refresh = time()
            return True
        else:
            return False

    @property
    def _remain(self):
        return self._target - self._progress

    @property
    def eta(self):
        if self.percentage:
            return (time() - self.start_time) / self.percentage * (100 - self.percentage)
