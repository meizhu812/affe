from time import sleep, time, strftime, localtime


class Console:
    P_HEAD = '>>>'
    P_FOOT = '###'
    P_FIX = [P_HEAD, P_FOOT]
    A_HEAD = '{:0>2d}>'
    A_FOOT = '{:0>2d}#'

    @staticmethod
    def output(msg: str):
        print(msg, flush=True, end='')
        return msg

    @staticmethod
    def warning_msg(msg: str):
        w_msg = '\n' + '[ WARNING: {0} ]'.format(msg)
        Console.output(w_msg)

    @staticmethod
    def cl():
        Console.output('\r{}\r'.format(80 * ' '))


class ApplyProgressBar:

    def __init__(self, *, apply_results: list):
        self._major_percentage = 0
        self._results = apply_results
        self._progress = 0
        self._target = len(apply_results)
        print(self._target)
        self.start_time = time()
        self.current_output = '[--------------------] ...starting...'

    def track_progress(self, t_refresh=0.1):
        while self.percentage < 100:
            self._refresh()
            sleep(t_refresh)

    def _refresh(self):
        self._update_progress()
        if self._major_advance:
            self._update_output()
        Console.cl()
        return Console.output(self.current_output)

    def _update_progress(self):
        self._progress = 0
        for result in self._results:
            if result.ready():
                self._progress += 1

    def _update_output(self):
        self.current_output = self._bar_output() + self._percentage_output() + self._eta_output()

    def _bar_output(self):
        n_blocks = int(self._major_percentage / 5)  # _major_percentage is int
        return '[{}{}]'.format(n_blocks * '+', (20 - n_blocks) * '-')  # e.g. '[++++++++++----------]'

    def _percentage_output(self):
        return '%3i%%' % self._major_percentage

    def _eta_output(self):
        if self.percentage == 100:
            return '...finished!\n'
        elif self.percentage >= 90:
            return '...almost done...'
        else:
            return '...%i seconds remaining...' % self.eta

    @property
    def percentage(self):
        return int(self._progress / self._target * 100)

    @property
    def _major_advance(self):
        if self.percentage - self._major_percentage >= 10:
            self._major_percentage = self.percentage // 10 * 10
            return True
        else:
            return False

    @property
    def _remain(self):
        return self._target - self._progress

    @property
    def eta(self):
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
                log_file.write(log_msg)
        Console.output(log_msg)

    def log_process(self, process_name, *, timed=True):
        def wrapper(process):
            def inner_wrapper(*args, **kwargs):
                self._action_phase = 0
                if self._process_phase == 0:
                    self.log(strftime('[%Y-%m-%d %H:%M] Project Started!\n', localtime(time())))
                self._process_phase += 1

                self.log(Logger.process_header(self._process_phase, process_name))
                start_time = time()
                returned = process(*args, **kwargs)
                run_time = time() - start_time

                if timed:
                    self.log(Logger.process_footer(self._process_phase, process_name, run_time))
                else:
                    self.log(Logger.process_footer(self._process_phase, process_name))

                return returned

            return inner_wrapper

        return wrapper

    def log_action(self, action_name, *, timed=True):
        def wrapper(action):
            def inner_wrapper(*args, **kwargs):
                self._action_phase += 1

                self.log(Logger.action_header(self._action_phase, action_name))
                start_time = time()
                returned = action(*args, **kwargs)
                run_time = time() - start_time

                if timed:
                    self.log(Logger.action_footer(self._action_phase, action_name, run_time))
                else:
                    self.log(Logger.action_footer(self._action_phase, action_name))

                return returned

            return inner_wrapper

        return wrapper

    @staticmethod
    def process_header(p_phase, p_name: str):
        ph = '>>> [Process Started] <{0:0>2d}> {1}\n'.format(p_phase, p_name)
        # e.g. '>>> [Process Started] <02> Reading Data from Files'
        return ph

    @staticmethod
    def process_msg(msg: str):
        pm = '||| {}'.format(msg)
        return pm

    @staticmethod
    def process_footer(p_phase, p_name: str, p_time=None):
        if p_time:
            time_str = '[Process Time: {0} seconds.]\n'.format(str(round(p_time, 2)))
        else:
            time_str = ''
        pf = '### [Process Finished] <{0:0>2d}> {1} {2}\n'.format(p_phase, p_name, time_str)
        # e.g. '### [Process Finished] <02> Reading Data from Files [Process Time: 19.93 seconds.]'
        return pf

    @staticmethod
    def action_header(a_phase, a_name: str):
        ah = '{0:0>2d}> {1}\n'.format(a_phase, a_name)
        # e.g. '01> Loading files to memory [Started]'
        return ah

    @staticmethod
    def action_msg(msg: str):
        am = '--- {}\n'.format(msg)
        return am

    @staticmethod
    def action_footer(a_phase, a_name: str, a_time=None):
        if a_time:
            time_str = '[Finished in {0} seconds]\n'.format(str(round(a_time, 2)))
        else:
            time_str = '[Finished]\n'
        af = '{0:0>2d}# {1} {2}\n'.format(a_phase, a_name, time_str)
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
