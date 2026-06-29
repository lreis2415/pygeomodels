from typing import Any, Dict, List, Optional

from pygeomodels.api import restapi_get
from pygeomodels.config import ModelEngineConfig
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
        self._categories_lang: Optional[str] = None
        self._models_ids = list()
        self._category_models: Dict[str, List[str]] = {}
        self._models_metadata = dict()
        self._models_caller = None
        self._ids_token = None
        self._ids_lang: Optional[str] = None
        self._metadata_token = None
        self._metadata_lang: Optional[str] = None
        self._caller_token = None
        self._models_basic_info: Dict[str, Dict[str, str]] = {}
        self._basic_info_token: Optional[str] = None
        self._basic_info_lang: Optional[str] = None

    def _resolve_token(
        self, access_token: Optional[str], *fallback_tokens: Optional[str]
    ) -> str:
        if access_token is not None and access_token.strip() != "":
            return access_token.strip()
        for token in fallback_tokens:
            if token is not None and str(token).strip() != "":
                return str(token).strip()
        raise ValueError("access_token is required")

    @staticmethod
    def _normalize_lang(lang: Optional[str]) -> str:
        """Normalize the language code used for localized API responses.

        Only 'cn' (Chinese) and 'en' (English) are supported. Anything else
        (None, empty, unknown values) falls back to 'en'.
        """
        if lang is None:
            return "en"
        normalized = str(lang).strip().lower()
        return normalized if normalized in ("cn", "en") else "en"

    def get_categories(
        self, access_token: Optional[str] = None, lang: str = "en"
    ) -> List[str]:
        lang = self._normalize_lang(lang)
        token = self._resolve_token(access_token, self._categories_token)
        if (
            self._categories is None
            or self._categories_token != token
            or self._categories_lang != lang
        ):
            self.set_categories(token, lang)
        return self._categories

    def set_categories(
        self, access_token: Optional[str] = None, lang: str = "en"
    ) -> None:
        lang = self._normalize_lang(lang)
        token = self._resolve_token(access_token, self._categories_token)
        # Use v2 API for catalog endpoints
        path = self.cfg.build_api_path(
            self.cfg.api_cls_modelmanager,
            self.cfg.api_mgt_generalmodel,
            self.cfg.api_gm_catalogcls,
            version_key="gm_catalog",
        )
        res = restapi_get(self.cfg.modelmanager_url, f"{path}?lang={lang}", token)
        if res is not None and (res["success"] == "true" or res["success"]):
            # v2 API returns nested structure: data.categories[].categories[]
            # Find the configured root catalog node and extract its child categories
            root_node = next(
                (
                    cat
                    for cat in res.get("data", {}).get("categories", [])
                    if cat.get("id") == self.cfg.api_gm_catalog_root_id
                ),
                None,
            )
            if root_node:
                self._categories = [
                    item["id"] for item in root_node.get("categories", [])
                ]
            else:
                self._categories = []
        else:
            print("Get categories list failed!")
            self._categories = []
        self._categories_token = token
        self._categories_lang = lang
        # Invalidate downstream caches since categories may have changed
        self._models_ids = []
        self._ids_token = None
        self._ids_lang = None
        self._models_metadata = {}
        self._metadata_token = None
        self._metadata_lang = None
        self._models_caller = None
        self._caller_token = None
        self._models_basic_info = {}
        self._basic_info_token = None
        self._basic_info_lang = None

    categories = property(get_categories, set_categories)

    def get_models_ids(self, access_token: Optional[str] = None, lang: str = "en"):
        lang = self._normalize_lang(lang)
        token = self._resolve_token(access_token, self._ids_token)
        if not self._models_ids or self._ids_token != token or self._ids_lang != lang:
            self.set_models_ids(token, lang)
        return self._models_ids

    def set_models_ids(self, access_token: Optional[str] = None, lang: str = "en"):
        lang = self._normalize_lang(lang)
        token = self._resolve_token(access_token, self._ids_token)
        # Ensure categories are loaded with the same language
        if (
            self._categories is None
            or self._categories_token != token
            or self._categories_lang != lang
        ):
            self.set_categories(token, lang)

        self._models_ids = []
        self._category_models = {}
        self._models_basic_info = {}
        if not self._categories:
            self._load_models_by_category(None, token, lang)
        else:
            for category_id in self._categories:
                self._load_models_by_category(category_id, token, lang)

        self._ids_token = token
        self._ids_lang = lang
        self._basic_info_token = token
        self._basic_info_lang = lang

    def _load_models_by_category(
        self,
        category_id: Optional[str],
        access_token: str,
        lang: str = "en",
    ) -> None:
        """
        根据categoryId加载模型ID，同时缓存 /list 返回的基础信息。

        Args:
            category_id: 类别ID，如果为None则获取所有模型
            lang: 返回内容的语言，'cn' 或 'en'，默认 'en'
        """
        lang = self._normalize_lang(lang)
        category_param = f"categoryId={category_id}" if category_id else "categoryId="
        # Use v2 API for model list endpoint
        path = self.cfg.build_api_path(
            self.cfg.api_cls_modelmanager,
            self.cfg.api_mgt_singlemodel,
            self.cfg.api_sm_list,
            version_key="sm_list",
        )
        res = restapi_get(
            self.cfg.modelmanager_url,
            f"{path}?modelName=&description=&{category_param}&semantic=&auditStatus=&page=&size=40&lang={lang}",
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
                        self._category_models.setdefault(category_id, []).append(
                            model_id
                        )
                    # 缓存 /list 返回的基础信息，避免后续对 /info 的大规模串行调用
                    identification = model.get("identification", {}) or {}
                    self._models_basic_info[model_id] = {
                        "display_name": identification.get("model_name", ""),
                        "description": identification.get("description", ""),
                        "model_unique_abbr": model.get("model_unique_abbr", ""),
                        "category_name": model.get("categoryName", ""),
                    }
            else:
                print(
                    f'Get models list for category "{category_id}" failed!\nError message: {res["message"]}'
                )
        else:
            print(f'Get models list for category "{category_id}" failed!')

    models_ids = property(get_models_ids, set_models_ids)

    def get_models_metadata(self, access_token: Optional[str] = None, lang: str = "en"):
        lang = self._normalize_lang(lang)
        token = self._resolve_token(access_token, self._metadata_token, self._ids_token)
        if (
            not self._models_metadata
            or self._metadata_token != token
            or self._metadata_lang != lang
        ):
            self.set_models_metadata(token, lang)
        return self._models_metadata

    def set_models_metadata(self, access_token: Optional[str] = None, lang: str = "en"):
        lang = self._normalize_lang(lang)
        token = self._resolve_token(access_token, self._metadata_token, self._ids_token)
        if not self._models_ids or self._ids_token != token or self._ids_lang != lang:
            self.set_models_ids(token, lang)

        self._models_metadata = {}
        for m_id in self._models_ids:
            # Model info API uses v1 /info endpoint
            res = restapi_get(
                self.cfg.modelmanager_url,
                "%s/%s/%s/%s/%s?lang=%s"
                % (
                    self.cfg.api_basename,
                    self.cfg.api_cls_modelmanager,
                    self.cfg.api_mgt_singlemodel,
                    m_id,
                    self.cfg.api_sm_info,
                    lang,
                ),
                token,
            )
            if res is None:
                continue
            if res["success"] == "true" or res["success"]:
                self._models_metadata[m_id] = res["data"]

        self._metadata_token = token
        self._metadata_lang = lang
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

    def list_all_models(
        self,
        access_token: Optional[str] = None,
        category: Optional[str] = None,
        lang: str = "en",
    ):
        lang = self._normalize_lang(lang)
        token = self._resolve_token(access_token, self._metadata_token, self._ids_token)
        if (
            not self._models_metadata
            or self._metadata_token != token
            or self._metadata_lang != lang
        ):
            self.set_models_metadata(token, lang)

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

    def list_all_models_lightweight(
        self,
        access_token: Optional[str] = None,
        category: Optional[str] = None,
        lang: str = "en",
    ) -> List[Dict[str, Any]]:
        """
        使用 /list 缓存数据返回模型列表，不调用 /info 接口（只需 1 个 /list 请求）。

        相比 list_all_models()，此方法避免了对每个模型串行调用 /info，
        大幅减少 HTTP 请求数量和响应时间。

        Note: 当 /list 接口已包含 model_unique_abbr 字段时，此方法也会返回该字段。

        Args:
            access_token: 访问令牌
            category: 类别过滤，None 表示全部模型
            lang: 返回内容语言，'cn' 或 'en'

        Returns:
            [{"model_id": "...", "display_name": "...", "description": "..."}, ...]
        """
        lang = self._normalize_lang(lang)
        token = self._resolve_token(access_token, self._ids_token)
        if (
            self._basic_info_token is None
            or self._basic_info_token != token
            or self._basic_info_lang != lang
        ):
            self.set_models_ids(token, lang)

        if category:
            model_ids = set(self._category_models.get(category, []))
        else:
            model_ids = None

        models_list = []
        for m_id, m_data in self._models_basic_info.items():
            if model_ids is not None and m_id not in model_ids:
                continue
            model_entry: Dict[str, Any] = {
                "model_id": m_id,
                "display_name": m_data.get("display_name", ""),
                "description": m_data.get("description", ""),
            }
            abbr = m_data.get("model_unique_abbr", "")
            if abbr:
                model_entry["model_unique_abbr"] = abbr
            category_name = m_data.get("category_name", "")
            if category_name:
                model_entry["category_name"] = category_name
            models_list.append(model_entry)
        return models_list

    def describe_model(
        self,
        model_name: str,
        access_token: Optional[str] = None,
        lang: str = "en",
    ) -> Optional[Dict[str, Any]]:
        lang = self._normalize_lang(lang)
        token = self._resolve_token(access_token, self._metadata_token, self._ids_token)
        if (
            not self._models_metadata
            or self._metadata_token != token
            or self._metadata_lang != lang
        ):
            self.set_models_metadata(token, lang)

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
