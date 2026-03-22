from pygeomodels.config import ModelEngineConfig
from pygeomodels.api import restapi_get, restapi_post


class modelTask(object):
    def __init__(self, cfg: ModelEngineConfig, project_id: str, access_token: str):
        self.cfg = cfg
        self.id = project_id
        if access_token is None or str(access_token).strip() == "":
            raise ValueError("access_token is required")
        self.access_token = str(access_token).strip()

    def data_info(self):
        res = restapi_get(
            self.cfg.modelmanager_url,
            "%s/%s/%s/%s"
            % (
                self.cfg.api_basename,
                self.cfg.api_cls_usrprj,
                self.id,
                self.cfg.api_uprj_data,
            ),
            self.access_token,
        )
        if res is None:
            return None
        if res["success"] == "true" or res["success"]:
            return res["data"]

    def log(self):
        res = restapi_get(
            self.cfg.modelmanager_url,
            "%s/%s/%s/%s"
            % (
                self.cfg.api_basename,
                self.cfg.api_cls_usrprj,
                self.id,
                self.cfg.api_uprj_log,
            ),
            self.access_token,
        )
        if res is None:
            return None
        if res["success"] == "true" or res["success"]:
            return res["data"]

    def progress(self):
        res = restapi_get(
            self.cfg.modelmanager_url,
            "%s/%s/%s/%s"
            % (
                self.cfg.api_basename,
                self.cfg.api_cls_usrprj,
                self.id,
                self.cfg.api_uprj_prog,
            ),
            self.access_token,
        )
        if res is None:
            return None
        if res["success"] == "true" or res["success"]:
            return res["data"]

    def stop(self):
        res = restapi_get(
            self.cfg.modelmanager_url,
            "%s/%s/%s/%s"
            % (
                self.cfg.api_basename,
                self.cfg.api_cls_usrprj,
                self.id,
                self.cfg.api_uprj_stop,
            ),
            self.access_token,
        )
        if res is None:
            return None
        if res["success"] == "true" or res["success"]:
            return "Stopped successfully!"

    def delete(self):
        res = restapi_post(
            self.cfg.modelmanager_url,
            "%s/%s/%s/%s"
            % (
                self.cfg.api_basename,
                self.cfg.api_cls_usrprj,
                self.id,
                self.cfg.api_uprj_del,
            ),
            {},
            self.access_token,
        )
        if res is None:
            return None
        if res["success"] == "true" or res["success"]:
            return "Deleted successfully!"
