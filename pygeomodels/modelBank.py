from pygeomodels.config import ModelEngineConfig
from pygeomodels.api import restapi_get
from pygeomodels.modelCaller import ModelCaller


class modelBank(object):
    """
    modelBank is a class that manages the models in the model bank.
    It is used to get the models ids, metadata, and caller.
    """
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
        # mbms/v1/model-manager/general-single-models/list
        res = restapi_get(self.cfg.modelmanager_url,
                          "%s/%s/%s/%s%s" % (self.cfg.api_basename, self.cfg.api_cls_modelmanager,
                                             self.cfg.api_mgt_singlemodel, self.cfg.api_sm_list,
                                             '?modelName=&description=&categoryId=&semantic=&auditStatus=&page='
                                             '&size=40'),
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
            # mbms/v1/model-manager/general-single-models/{id}/info
            res = restapi_get(self.cfg.modelmanager_url,
                              "%s/%s/%s/%s/%s" % (self.cfg.api_basename, self.cfg.api_cls_modelmanager,
                                                  self.cfg.api_mgt_singlemodel, m_id, self.cfg.api_sm_info),
                              self.cfg.token)
            if res is None:
                continue
            if res['success'] == 'true' or res['success']:
                self._models_metadata[m_id] = res['data']

    models_metadata = property(get_models_metadata, set_models_metadata)

    def list_all_models(self):
        if not self._models_metadata:
            self.set_models_metadata()
        
        models_list = []
        for m_id, m_data in self._models_metadata.items():
            models_list.append({
                "model_id": m_id,
                "name": m_data.get('model_unique_abbr', ''),
                "description": m_data.get('identification', {}).get('description', '')
            })
        return models_list

    def describe_model(self, model_id: str):
        if not self._models_metadata:
            self.set_models_metadata()

        model_data = self._models_metadata.get(model_id)
        if model_data is None:
            return None

        # Assuming inputs, params, outputs are directly available in model_data
        # You may need to adjust this based on the actual structure of your model metadata
        return {
            "model_data": model_data
        }

    def get_models_caller(self):
        if self._models_caller is None:
            self.set_models_caller()
        return self._models_caller

    def set_models_caller(self):
        self._models_caller = ModelCaller(self.cfg, self.models_metadata)

    models_caller = property(get_models_caller, set_models_caller)
