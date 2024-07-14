
# base_url = 'http://47.243.118.35:7504/mbms'
base_url_local = 'http://127.0.0.1:7504/mbms'
base_url_k8s = 'http://modelmanager:7504/mbms'

catogory_api = '/category'
models_api = '/models'
task_api = '/tasks'


def get_base_url(mode='prod', addr='127.0.0.1'):
    if mode == 'prod':
        return base_url_k8s
    elif mode == 'local':
        return base_url_local
    elif mode == 'external':
        return 'http://%s:7504/mbms' % addr
    else:
        return base_url_k8s
