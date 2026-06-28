from typing import Any, Dict, List, Optional

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
        self._categories: Optional[List[str]] = None
        self._categories_token: Optional[str] = None
        self._models_ids = list()
        self._category_models: Dict[str, List[str]] = {}
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

    def get_categories(self, access_token: Optional[str] = None) -> List[str]:
        token = self._resolve_token(access_token, self._categories_token)
        if self._categories is None or self._categories_token != token:
            self.set_categories(token)
        return self._categories

    def set_categories(self, access_token: Optional[str] = None) -> None:
        token = self._resolve_token(access_token, self._categories_token)
        # Use v2 API for catalog endpoints
        path = self.cfg.build_api_path(
            self.cfg.api_cls_modelmanager,
            self.cfg.api_mgt_generalmodel,
            self.cfg.api_gm_catalogcls,
            version_key='gm_catalog'
        )
        res = restapi_get(self.cfg.modelmanager_url, path, token)
        if res is not None and (res["success"] == "true" or res["success"]):
            self._categories = [
                item["id"] for item in res.get("data", {}).get("categories", [])
            ]
        else:
            print("Get categories list failed!")
            self._categories = []
        self._categories_token = token
        # Invalidate downstream caches since categories may have changed
        self._models_ids = []
        self._ids_token = None
        self._models_metadata = {}
        self._metadata_token = None
        self._models_caller = None
        self._caller_token = None

    categories = property(get_categories, set_categories)

    def get_models_ids(self, access_token: Optional[str] = None):
        token = self._resolve_token(access_token, self._ids_token)
        if not self._models_ids or self._ids_token != token:
            self.set_models_ids(token)
        return self._models_ids

    def set_models_ids(self, access_token: Optional[str] = None):
        token = self._resolve_token(access_token, self._ids_token)
        # Ensure categories are loaded
        if self._categories is None or self._categories_token != token:
            self.set_categories(token)

        self._models_ids = []
        self._category_models = {}
        if not self._categories:
            self._load_models_by_category(None, token)
        else:
            for category_id in self._categories:
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
                    if category_id:
                        self._category_models.setdefault(category_id, []).append(model_id)
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

    def _classify_parameter_bucket(self, parameter: Dict[str, Any]) -> str:
        param_type = str(parameter.get("param_type", "")).strip().lower()
        if param_type == "input_data":
            return "inputs"
        if param_type == "output_data":
            return "outputs"
        return "params"

    def _build_run_template(
        self, model_name: str, parameters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        template: Dict[str, Any] = {
            "model_name": model_name,
            "inputs": {},
            "params": {},
            "outputs": {},
            "task_name": "",
        }

        for parameter in parameters:
            if not bool(parameter.get("is_required", False)):
                continue
            bucket = self._classify_parameter_bucket(parameter)
            key = parameter.get("arg_name") or parameter.get("name")
            if key:
                specification = parameter.get("specification", {}) or {}
                template[bucket][key] = specification.get("default")

        return template

    def list_all_models(self, access_token: Optional[str] = None, category: Optional[str] = None):
        token = self._resolve_token(access_token, self._metadata_token, self._ids_token)
        if not self._models_metadata or self._metadata_token != token:
            self.set_models_metadata(token)

        if category:
            model_ids = set(self._category_models.get(category, []))
        else:
            model_ids = None

        models_list = []
        for m_id, m_data in self._models_metadata.items():
            if model_ids is not None and m_id not in model_ids:
                continue
            models_list.append(
                {
                    "model_name": m_data.get("model_unique_abbr", ""),
                    "model_description": m_data.get("identification", {}).get(
                        "description", ""
                    ),
                }
            )
        return models_list

    def describe_model(
        self, model_name: str, access_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        token = self._resolve_token(access_token, self._metadata_token, self._ids_token)
        if not self._models_metadata or self._metadata_token != token:
            self.set_models_metadata(token)

        for _, model_data in self._models_metadata.items():
            if model_data.get("model_unique_abbr", "") == model_name:
                description = model_data.get("identification", {}).get(
                    "description", ""
                )
                parameters = model_data.get("parameter_info", {}).get("parameters", [])

                visible_parameters = [
                    p for p in parameters if bool(p.get("visible", False))
                ]
                run_template = self._build_run_template(model_name, visible_parameters)

                return {
                    "model_name": model_name,
                    "description": description,
                    "run_template": run_template,
                    "parameter_info": {
                        "parameters": visible_parameters,
                    },
                }
        return None

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
