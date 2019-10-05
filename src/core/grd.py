
from core.base import BaseData
class GrdData(BaseData):
    def _load_data(self):
        with open(self.data_path,'r') as f:

