from configparser import ConfigParser

from util.logger import ConsoleLogger


class BaseData:
    def __init__(self):
        pass


class BaseModule:
    def __init__(self, *, config: ConfigParser):
        self._config = config
        self._parse_config()

    def _parse_config(self):
        raise NotImplementedError
