from typing import Any, Dict, Optional, Callable

from pygeomodels.config import ModelEngineConfig
from pygeomodels.api import restapi_post
from pygeomodels.utils import generate_uniqueid


class ModelCaller:
    def __init__(self, cfg: ModelEngineConfig, metadata: Dict[str, Dict[str, Optional[Any]]]):
        self.cfg = cfg
        self.mmeta = metadata
        self.model_functions = self._generate_model_functions()

    def _generate_model_functions(self):
        model_functions = dict()

        for (m_id, m_data) in self.mmeta.items():
            m_name = m_data['model_unique_abbr']

            def create_model_function(_id, _name):
                def model_function(_inputs: Dict[str, Optional[Any]],
                                   _params: Dict[str, Optional[Any]],
                                   _outputs: Dict[str, Optional[Any]],
                                   _taskname: str = '') -> Optional[Dict[str, Optional[Any]]]:
                    # Using model-runner to start a task. Deprecated.
                    # mbms/v1/model-runner/single-models/{id}/run
                    # method = "%s/%s/%s/%s/%s" % (self.cfg.api_basename, self.cfg.api_cls_runner,
                    #                              self.cfg.api_run_singlemodel, _id, self.cfg.api_srun_run)

                    # Using user-projects to start a model computation.
                    # mbms/v1/user-projects/single-models/{id}/run
                    method = "%s/%s/%s/%s/%s" % (self.cfg.api_basename, self.cfg.api_cls_usrprj,
                                                 self.cfg.api_uprj_single, _id, self.cfg.api_sprj_run)
                    if _taskname == '':
                        _taskname = 'code-%s-%s' % (_name, str(next(generate_uniqueid())))
                    post_body = {
                        "params": [
                        ],
                        "task_name": _taskname
                    }

                    for ik, iv in _inputs.items():
                        post_body['params'].append({'param_name': ik, 'param_value': iv})
                    for pk, pv in _params.items():
                        post_body['params'].append({'param_name': pk, 'param_value': pv})
                    for ok, ov in _outputs.items():
                        post_body['params'].append({'param_name': ok, 'param_value': ov})
                    res = restapi_post(self.cfg.modelmanager_url, method, post_body, self.cfg.token)
                    if res is None:
                        return None
                    if res['success'] == 'true' or res['success']:
                        return res['data']['project_id']

                return model_function

            model_function = create_model_function(m_id, m_name)
            model_function.__name__ = m_name
            model_function.__annotations__ = {
                'inputs': Dict[str, Any],
                'params': Dict[str, Any],
                'outputs': Dict[str, Any],
                'return': Dict[str, Any]
            }

            model_functions[m_name] = model_function

        return model_functions

    def __getattr__(self, name: str) -> Callable:
        if name in self.model_functions:
            return self.model_functions[name]
        raise AttributeError(f"No such model: {name}")
