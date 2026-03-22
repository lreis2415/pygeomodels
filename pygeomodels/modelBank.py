from typing import List, Optional

from pygeomodels.config import ModelEngineConfig
from pygeomodels.api import restapi_get
from pygeomodels.modelCaller import ModelCaller


class modelBank(object):
    """
    modelBank is a class that manages the models in the model bank.
    It is used to get the models ids, metadata, and caller.
    """

    def __init__(
        self, cfg: ModelEngineConfig, category_ids: Optional[List[str]] = None
    ):
        self.cfg = cfg
        self._category_ids = category_ids  # 存储类别列表
        self._models_ids = list()
        self._models_metadata = dict()
        self._models_caller = None
        self._ids_token = None
        self._metadata_token = None
        self._caller_token = None

    def _resolve_token(
        self, access_token: Optional[str], *fallback_tokens: Optional[str]
    ) -> str:
        if access_token is not None and access_token.strip() != "":
            return access_token.strip()
        for token in fallback_tokens:
            if token is not None and str(token).strip() != "":
                return str(token).strip()
        raise ValueError("access_token is required")

    def get_models_ids(self, access_token: Optional[str] = None):
        token = self._resolve_token(access_token, self._ids_token)
        if not self._models_ids or self._ids_token != token:
            self.set_models_ids(token)
        return self._models_ids

    def set_models_ids(self, access_token: Optional[str] = None):
        token = self._resolve_token(access_token, self._ids_token)
        self._models_ids = []

        # 如果没有指定类别，保持原有行为（获取所有）
        if self._category_ids is None or len(self._category_ids) == 0:
            self._load_models_by_category(None, token)
        else:
            # 遍历每个类别，逐个加载模型ID（API不支持列表）
            for category_id in self._category_ids:
                self._load_models_by_category(category_id, token)

        self._ids_token = token

    def _load_models_by_category(
        self, category_id: Optional[str], access_token: str
    ) -> None:
        """
        根据categoryId加载模型ID

        Args:
            category_id: 类别ID，如果为None则获取所有模型
        """
        category_param = f"categoryId={category_id}" if category_id else "categoryId="
        res = restapi_get(
            self.cfg.modelmanager_url,
            "%s/%s/%s/%s%s"
            % (
                self.cfg.api_basename,
                self.cfg.api_cls_modelmanager,
                self.cfg.api_mgt_singlemodel,
                self.cfg.api_sm_list,
                f"?modelName=&description=&{category_param}&semantic=&auditStatus=&page=&size=40",
            ),
            access_token,
        )
        if res is not None:
            if res["success"] == "true" or res["success"]:
                modellist = res["data"]["content"]
                for model in modellist:
                    model_id = model["model_id"]
                    # 避免重复添加
                    if model_id not in self._models_ids:
                        self._models_ids.append(model_id)
            else:
                print(
                    f'Get models list for category "{category_id}" failed!\nError message: {res["message"]}'
                )
        else:
            print(f'Get models list for category "{category_id}" failed!')

    models_ids = property(get_models_ids, set_models_ids)

    def get_models_metadata(self, access_token: Optional[str] = None):
        token = self._resolve_token(access_token, self._metadata_token, self._ids_token)
        if not self._models_metadata or self._metadata_token != token:
            self.set_models_metadata(token)
        return self._models_metadata

    def set_models_metadata(self, access_token: Optional[str] = None):
        token = self._resolve_token(access_token, self._metadata_token, self._ids_token)
        if not self._models_ids or self._ids_token != token:
            self.set_models_ids(token)

        self._models_metadata = {}
        for m_id in self._models_ids:
            # mbms/v1/model-manager/general-single-models/{id}/info
            res = restapi_get(
                self.cfg.modelmanager_url,
                "%s/%s/%s/%s/%s"
                % (
                    self.cfg.api_basename,
                    self.cfg.api_cls_modelmanager,
                    self.cfg.api_mgt_singlemodel,
                    m_id,
                    self.cfg.api_sm_info,
                ),
                token,
            )
            if res is None:
                continue
            if res["success"] == "true" or res["success"]:
                self._models_metadata[m_id] = res["data"]

        self._metadata_token = token
        self._models_caller = None
        self._caller_token = None

    models_metadata = property(get_models_metadata, set_models_metadata)

    def list_all_models(self, access_token: Optional[str] = None):
        token = self._resolve_token(access_token, self._metadata_token, self._ids_token)
        if not self._models_metadata or self._metadata_token != token:
            self.set_models_metadata(token)

        models_list = []
        for m_id, m_data in self._models_metadata.items():
            models_list.append(
                {
                    "model_id": m_id,
                    "name": m_data.get("model_unique_abbr", ""),
                    "description": m_data.get("identification", {}).get(
                        "description", ""
                    ),
                }
            )
        return models_list

    def describe_model(self, model_id: str, access_token: Optional[str] = None):
        token = self._resolve_token(access_token, self._metadata_token, self._ids_token)
        if not self._models_metadata or self._metadata_token != token:
            self.set_models_metadata(token)

        model_data = self._models_metadata.get(model_id)
        if model_data is None:
            return None

        # Assuming inputs, params, outputs are directly available in model_data
        # You may need to adjust this based on the actual structure of your model metadata
        return {"model_data": model_data}

    def get_models_caller(self, access_token: Optional[str] = None):
        token = self._resolve_token(
            access_token, self._caller_token, self._metadata_token, self._ids_token
        )
        if self._models_caller is None or self._caller_token != token:
            self.set_models_caller(token)
        return self._models_caller

    def set_models_caller(self, access_token: Optional[str] = None):
        token = self._resolve_token(
            access_token, self._caller_token, self._metadata_token, self._ids_token
        )
        if not self._models_metadata or self._metadata_token != token:
            self.set_models_metadata(token)
        self._models_caller = ModelCaller(self.cfg, self._models_metadata)
        self._caller_token = token

    models_caller = property(get_models_caller, set_models_caller)
