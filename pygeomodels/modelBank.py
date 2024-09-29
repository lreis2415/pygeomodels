from pygeomodels.config import ModelEngineConfig
from pygeomodels.api import restapi_get
from pygeomodels.modelCaller import ModelCaller


class modelBank(object):
    def __init__(self, cfg: ModelEngineConfig):
        self.cfg = cfg
        self._models_ids = list()
        self._models_metadata = dict()
        self._models_caller = None

    def get_models_ids(self):
        if not self._models_ids:
            self.set_models_ids()
        return self._models_ids

    def set_models_ids(self):
        res = restapi_get(self.cfg.modelmanager_url,
                          "%s/%s/%s/%s%s" % (self.cfg.api_basename, self.cfg.api_cls_modelmanager,
                                             self.cfg.api_mgt_singlemodel, self.cfg.api_sm_list,
                                             '?modelName=&description=&categoryId=&semantic=&auditStatus=&page='
                                             '&size=200'),
                          self.cfg.token)
        if res is not None:
            if res['success'] == 'true' or res['success']:
                modellist = res['data']['content']
                for model in modellist:
                    self._models_ids.append(model['model_id'])
            else:
                print('Get models list failed!\nError message: %s' % res['message'])
        else:
            print('Get models list failed!')

    models_ids = property(get_models_ids, set_models_ids)

    def get_models_metadata(self):
        if not self._models_metadata:
            self.set_models_metadata()
        return self._models_metadata

    def set_models_metadata(self):
        if not self._models_ids:
            self.set_models_ids()
        for m_id in self._models_ids:
            res = restapi_get(self.cfg.modelmanager_url,
                              "%s/%s/%s/%s/%s" % (self.cfg.api_basename, self.cfg.api_cls_modelmanager,
                                                  self.cfg.api_mgt_singlemodel, m_id, self.cfg.api_sm_info),
                              self.cfg.token)
            if res is None:
                continue
            if res['success'] == 'true' or res['success']:
                self._models_metadata[m_id] = res['data']

    models_metadata = property(get_models_metadata, set_models_metadata)

    def get_models_caller(self):
        if self._models_caller is None:
            self.set_models_caller()
        return self._models_caller

    def set_models_caller(self):
        self._models_caller = ModelCaller(self.cfg, self.models_metadata)

    models_caller = property(get_models_caller, set_models_caller)
