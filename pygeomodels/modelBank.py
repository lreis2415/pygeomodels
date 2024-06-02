from pygeomodels.api import *
from pygeomodels.modelCaller import ModelCaller


class modelBank(object):
    def __init__(self):
        self.models_api_full = base_url + models_api
        self.models_list_api_full = self.models_api_full + '?isDetailed=false'
        self._models_ids = list()
        self._models_metadata = dict()
        self._models_caller = None

    def get_models_ids(self):
        if not self._models_ids:
            self.set_models_ids()
        return self._models_ids

    def set_models_ids(self):
        self._models_ids = get_models_list()

    models_ids = property(get_models_ids, set_models_ids)

    def get_models_metadata(self):
        if not self._models_metadata:
            self.set_models_metadata()
        return self._models_metadata

    def set_models_metadata(self):
        for m_id in self.models_ids:
            m_meta = get_model_metadata(m_id)
            if m_meta:
                self._models_metadata[m_id] = m_meta

    models_metadata = property(get_models_metadata, set_models_metadata)

    def get_models_caller(self):
        if self._models_caller is None:
            self.set_models_caller()
        return self._models_caller

    def set_models_caller(self):
        self._models_caller = ModelCaller(self.models_metadata)

    models_caller = property(get_models_caller, set_models_caller)
