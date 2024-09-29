from pygeomodels.config import ModelEngineConfig
from pygeomodels.api import restapi_get, restapi_post


class modelTask(object):
    def __init__(self, cfg: ModelEngineConfig, project_id: str):
        self.cfg = cfg
        self.id = project_id

    def data_info(self):
        res = restapi_get(self.cfg.modelmanager_url,
                          "%s/%s/%s/%s" % (self.cfg.api_basename, self.cfg.api_cls_usrprj,
                                           self.id, self.cfg.api_uprj_data),
                          self.cfg.token)
        if res is None:
            return None
        if res['success'] == 'true' or res['success']:
            return res['data']

    def log(self):
        res = restapi_get(self.cfg.modelmanager_url,
                          "%s/%s/%s/%s" % (self.cfg.api_basename, self.cfg.api_cls_usrprj,
                                           self.id, self.cfg.api_uprj_log),
                          self.cfg.token)
        if res is None:
            return None
        if res['success'] == 'true' or res['success']:
            return res['data']

    def progress(self):
        res = restapi_get(self.cfg.modelmanager_url,
                          "%s/%s/%s/%s" % (self.cfg.api_basename, self.cfg.api_cls_usrprj,
                                           self.id, self.cfg.api_uprj_prog),
                          self.cfg.token)
        if res is None:
            return None
        if res['success'] == 'true' or res['success']:
            return res['data']

    def stop(self):
        res = restapi_get(self.cfg.modelmanager_url,
                          "%s/%s/%s/%s" % (self.cfg.api_basename, self.cfg.api_cls_usrprj,
                                           self.id, self.cfg.api_uprj_stop),
                          self.cfg.token)
        if res is None:
            return None
        if res['success'] == 'true' or res['success']:
            return 'Stopped successfully!'

    def delete(self):
        res = restapi_post(self.cfg.modelmanager_url,
                           "%s/%s/%s/%s" % (self.cfg.api_basename, self.cfg.api_cls_usrprj,
                                            self.id, self.cfg.api_uprj_del),
                           {}, self.cfg.token)
        if res is None:
            return None
        if res['success'] == 'true' or res['success']:
            return 'Deleted successfully!'
