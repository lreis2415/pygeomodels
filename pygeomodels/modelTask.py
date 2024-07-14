from pygeomodels.api import get_task_status
from pygeomodels.config import get_base_url, task_api

class modelTask(object):
    def __init__(self, mode='prod', addr='127.0.0.1'):
        self.base_url = get_base_url(mode, addr)
        self.task_api_full = self.base_url + task_api

    def get_status(self, tid):
        return get_task_status(self.base_url, tid)

