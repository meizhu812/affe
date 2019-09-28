from time import sleep, time, strftime, localtime


class Console:
    P_HEAD = '>>>'
    P_FOOT = '###'
    P_FIX = [P_HEAD, P_FOOT]
    A_HEAD = '{:0>2d}>'
    A_FOOT = '{:0>2d}#'

    @staticmethod
    def output(msg: str, end='\n'):
        print(msg, flush=True, end=end)
        return msg

    @staticmethod
    def warning_msg(msg: str):
        w_msg = '\n' + '[ WARNING: {0} ]'.format(msg)
        Console.output(w_msg)

    @staticmethod
    def cl():
        Console.output('\r{}\r'.format(80 * ' '), end='')

    @staticmethod
    def blk(lines):
        Console.output(lines * '\n', end='')


class ProgressBar:
    def __init__(self, target, interval=5):
        self._major_percentage = 0
        self._progress = 0
        self._target = target
        self._interval = interval
        self._t_last_refresh = time()
        self.start_time = time()
        Console.output('[--------------------]......starting...', end='')

    def update(self, result=None):
        self._update_progress()
        if self._refresh_ready:
            self._update_output()
            Console.cl()
            Console.output(self.current_output, end='')

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
        elif self.percentage >= 25:  # the eta becomes stable
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


class Logger:
    def __init__(self, log_path: str = ''):
        self._log_path = ''
        if log_path:
            self.set_log_path(log_path)
        self._logs = []
        self._process_phase = self._action_phase = 0

    def set_log_path(self, log_path: str):
        self._log_path = log_path

    def log(self, log_msg):
        if self._log_path:
            with open(self._log_path, 'a') as log_file:
                log_file.write(strftime('[%Y-%m-%d %H:%M]', localtime(time())) + log_msg + '\n')
        Console.output(log_msg)

    def log_process(self, process_name, *, timed=True):
        def wrapper(process):
            def inner_wrapper(*args, **kwargs):
                self._action_phase = 0
                if self._process_phase == 0:
                    self.log('{0} Project Started! {0}'.format(20 * '*'))
                self._process_phase += 1

                self.log(Logger._process_header(self._process_phase, process_name))
                start_time = time()
                returned = process(*args, **kwargs)
                run_time = time() - start_time

                if timed:
                    self.log(Logger._process_footer(self._process_phase, process_name, run_time))
                else:
                    self.log(Logger._process_footer(self._process_phase, process_name))

                Console.blk(2)

                return returned

            return inner_wrapper

        return wrapper

    def log_action(self, action_name, *, timed=True):
        def wrapper(action):
            def inner_wrapper(*args, **kwargs):
                self._action_phase += 1

                self.log(Logger._action_header(self._action_phase, action_name))
                start_time = time()
                returned = action(*args, **kwargs)
                run_time = time() - start_time

                if timed:
                    self.log(Logger._action_footer(self._action_phase, action_name, run_time))
                else:
                    self.log(Logger._action_footer(self._action_phase, action_name))

                Console.blk(1)

                return returned

            return inner_wrapper

        return wrapper

    @staticmethod
    def _process_header(p_phase, p_name: str):
        ph = '>>> [Process Started] <{0:0>2d}> {1}'.format(p_phase, p_name)
        # e.g. '>>> [Process Started] <02> Reading Data from Files'
        return ph

    @staticmethod
    def _process_msg(msg: str):
        pm = '||| {}'.format(msg)
        return pm

    @staticmethod
    def _process_footer(p_phase, p_name: str, p_time=None):
        if p_time:
            time_str = '[Process Time: {0} seconds.]'.format(str(round(p_time, 2)))
        else:
            time_str = ''
        pf = '### [Process Finished] <{0:0>2d}> {1} {2}'.format(p_phase, p_name, time_str)
        # e.g. '### [Process Finished] <02> Reading Data from Files [Process Time: 19.93 seconds.]'
        return pf

    @staticmethod
    def _action_header(a_phase, a_name: str):
        ah = '{0:0>2d}> {1}'.format(a_phase, a_name)
        # e.g. '01> Loading files to memory [Started]'
        return ah

    @staticmethod
    def _action_msg(msg: str):
        am = '--- {}'.format(msg)
        return am

    @staticmethod
    def _action_footer(a_phase, a_name: str, a_time=None):
        if a_time:
            time_str = '[Finished in {0} seconds]'.format(str(round(a_time, 2)))
        else:
            time_str = '[Finished]'
        af = '{0:0>2d}# {1} {2}'.format(a_phase, a_name, time_str)
        # e.g. '01# Loading files to memory [Finished in 8.12 seconds]'
        return af


'''
class StopWatch:
    def __init__(self, *, start_now: bool):
        self._start_time = self._lap_start_time = self._lap_time = self._split_time = None
        self._on = False
        self.error = False
        if start_now:
            self.start()

    def start(self):
        if not self._on:
            self._start_time = self._lap_start_time = self._split_time = time()
            self._on = True
        else:
            Console.warning_msg('The timer has already been started, check code for duplicate start commands!')
            self.error = True

    def split(self):
        self._split_time = time() - self._start_time
        return self._split_time

    def lap(self):
        self._lap_time = time() - self._lap_start_time
        self._lap_start_time = time()
        return self._lap_time

    def reset(self, *, start_now: bool):
        self.
        self.__init__(start_now=start_now)

    def stop(self):
        if self._on:
            self.split()
            self.lap()
            self._on = False
        else:
            Console.warning_msg('The timer has already been stopped, check code for duplicate stop commands!')
            self.error = True
'''