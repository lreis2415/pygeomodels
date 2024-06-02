import requests
from typing import Any, Dict, List, Optional

from pygeomodels.config import *
from pygeomodels.utils import generate_uniqueid


def get_models_list() -> List[str]:
    models_list_api_full = base_url + models_api + '?isDetailed=false'
    resp = requests.get(models_list_api_full).json()
    models_ids = list()
    if resp['success']:
        modellist = resp['data']
        for model in modellist:
            models_ids.append(model['model_id'])
    else:
        print('Get models list failed!\nError code: %d\n Error message: %s' % (resp['code'], resp['message']))
    return models_ids


def get_model_metadata(model_id: str) -> Dict[str, Optional[Any]]:
    getmodel_api_full = base_url + models_api + ('/%s' % model_id) + '?page=1&size=20'
    resp = requests.get(getmodel_api_full).json()
    if resp['success']:
        return resp['data']
    else:
        print('Get model metadata failed!\nError code: %d\n Error message: %s' % (resp['code'], resp['message']))
        return {}


def submit_model_task(model_id: str,
                      inputs: Dict[str, Optional[Any]],
                      params: Dict[str, Optional[Any]],
                      outputs: Dict[str, Optional[Any]],
                      taskname: str = '') -> Dict[str, Optional[Any]]:
    modelapi = base_url + models_api + ('/%s/task' % model_id)
    if taskname == '':
        taskname = 'notebook-' + str(next(generate_uniqueid()))
    post_body = {
        "params": [
        ],
        "task_name": taskname
    }

    for it in inputs:
        post_body['params'].append({'param_name': it, 'param_value': inputs[it]})
    for it in params:
        post_body['params'].append({'param_name': it, 'param_value': params[it]})
    for it in outputs:
        post_body['params'].append({'param_name': it, 'param_value': outputs[it]})
    response = requests.post(modelapi, json=post_body)
    return response.json()


def get_task_status(task_id: str) -> Dict[str, Optional[Any]]:
    gettask_api_full = base_url + task_api + ('/%s' % task_id)
    resp = requests.get(gettask_api_full).json()
    if resp['success']:
        return resp['data']
    else:
        print('Get model metadata failed!\nError code: %d\n Error message: %s' % (resp['code'], resp['message']))
        return {}


if __name__ == "__main__":
    pass
    
