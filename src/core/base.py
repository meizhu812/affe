from configparser import ConfigParser

from util.logger import ConsoleLogger


class BaseData:
    def __init__(self):
        pass


class BaseModule:
    def __init__(self, config: ConfigParser, logger: ConsoleLogger):
        self._config = config
        self._logger = logger
        self._parse_config()

    def _parse_config(self):
        raise NotImplementedError
