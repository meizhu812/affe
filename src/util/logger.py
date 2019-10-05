from time import strftime, localtime, time

from util.consle import console


class Logger:
    def log(self, *args, **kwargs):
        raise NotImplementedError

    def log_process(self, *args, **kwargs):
        raise NotImplementedError

    def log_action(self, *args, **kwargs):
        raise NotImplementedError


class ConsoleLogger(Logger):
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
        console.output(log_msg)

    def log_process(self, process_name, *, timed=True):
        def wrapper(process):
            def inner_wrapper(*args, **kwargs):
                self._action_phase = 0
                if self._process_phase == 0:
                    self.log('{0} Project Started! {0}'.format(20 * '*'))
                self._process_phase += 1

                self.log(self._process_header(self._process_phase, process_name))
                start_time = time()
                returned = process(*args, **kwargs)
                run_time = time() - start_time

                if timed:
                    self.log(self._process_footer(self._process_phase, process_name, run_time))
                else:
                    self.log(self._process_footer(self._process_phase, process_name))

                console.blk(2)

                return returned

            return inner_wrapper

        return wrapper

    def log_action(self, action_name, *, timed=True):
        def wrapper(action):
            def inner_wrapper(*args, **kwargs):
                self._action_phase += 1

                self.log(self._action_header(self._action_phase, action_name))
                start_time = time()
                returned = action(*args, **kwargs)
                run_time = time() - start_time

                if timed:
                    self.log(self._action_footer(self._action_phase, action_name, run_time))
                else:
                    self.log(self._action_footer(self._action_phase, action_name))

                console.blk(1)

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


logger = ConsoleLogger()
