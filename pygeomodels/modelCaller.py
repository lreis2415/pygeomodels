import re
from typing import Any, Callable, Dict, Optional

import httpx

from pygeomodels.config import ModelEngineConfig
from pygeomodels.api import restapi_post
from pygeomodels.utils import generate_uniqueid


class ModelSubmissionError(RuntimeError):
    """A safe, actionable failure returned while starting a model task."""

    _MAX_CODE_LENGTH = 128
    _MAX_MESSAGE_LENGTH = 500
    _BEARER_TOKEN_PATTERN = re.compile(r"(?i)(bearer\s+)[^\s,;]+")
    _ACCESS_TOKEN_PATTERN = re.compile(
        r"(?i)(access_token\s*[=:]\s*[\"']?)[^\s,;\"']+"
    )

    def __init__(
        self,
        reason: str,
        *,
        status_code: Optional[int] = None,
        success: Optional[bool] = None,
        code: Optional[object] = None,
        backend_message: Optional[object] = None,
    ):
        self.reason = reason
        self.status_code = status_code
        self.success = success
        self.code = self._bounded_text(code, self._MAX_CODE_LENGTH)
        self.backend_message = self._bounded_text(
            backend_message, self._MAX_MESSAGE_LENGTH
        )

        details = []
        if status_code is not None:
            details.append(f"status_code={status_code}")
        if success is not None:
            details.append(f"success={success}")
        if self.code:
            details.append(f"code={self.code}")
        if self.backend_message:
            details.append(f"message={self.backend_message}")
        detail_text = f" ({', '.join(details)})" if details else ""
        super().__init__(f"Model submission failed: {reason}{detail_text}")

    @staticmethod
    def _bounded_text(value: Optional[object], maximum: int) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        text = ModelSubmissionError._BEARER_TOKEN_PATTERN.sub(
            r"\1[REDACTED]", text
        )
        text = ModelSubmissionError._ACCESS_TOKEN_PATTERN.sub(
            r"\1[REDACTED]", text
        )
        return text[:maximum] if text else None


def _parse_success(value: object) -> Optional[bool]:
    """Return a normalized backend success flag, or None when malformed."""
    if value is True or value == "true":
        return True
    if value is False or value == "false":
        return False
    return None


class ModelCaller:
    """
    ModelCaller is a class that generates model functions for each model.
    It is used to call the model functions.
    """

    def __init__(
        self, cfg: ModelEngineConfig, metadata: Dict[str, Dict[str, Optional[Any]]]
    ):
        self.cfg = cfg
        self.mmeta = metadata
        self.model_functions = self._generate_model_functions()

    def _generate_model_functions(self):
        model_functions = dict()

        for m_id, m_data in self.mmeta.items():
            m_name = m_data["model_unique_abbr"]

            def create_model_function(_id, _name):
                def model_function(request_body: Dict[str, Any]) -> Optional[str]:
                    _inputs = request_body.get("inputs", {})
                    _params = request_body.get("params", {})
                    _outputs = request_body.get("outputs", {})
                    _taskname = request_body.get("task_name", "")
                    _model_id = request_body.get("model_id", _id)
                    _access_token = request_body.get("access_token")
                    if _access_token is None or str(_access_token).strip() == "":
                        raise ValueError(
                            "access_token must be provided in the request body."
                        )

                    # Using user-projects to start a model computation.
                    # mbms/v1/user-projects/single-models/{id}/run
                    method = "%s/%s/%s/%s/%s" % (
                        self.cfg.api_basename,
                        self.cfg.api_cls_usrprj,
                        self.cfg.api_uprj_single,
                        _model_id,
                        self.cfg.api_sprj_run,
                    )
                    if _taskname == "":
                        _taskname = "mcp-%s-%s" % (
                            _name,
                            str(next(generate_uniqueid())),
                        )
                    post_body = {"params": [], "task_name": _taskname}

                    for ik, iv in _inputs.items():
                        post_body["params"].append(
                            {"param_name": ik, "param_value": iv}
                        )
                    for pk, pv in _params.items():
                        post_body["params"].append(
                            {"param_name": pk, "param_value": pv}
                        )
                    for ok, ov in _outputs.items():
                        post_body["params"].append(
                            {"param_name": ok, "param_value": ov}
                        )
                    try:
                        res = restapi_post(
                            self.cfg.modelmanager_url,
                            method,
                            post_body,
                            str(_access_token).strip(),
                            raise_on_error=True,
                        )
                    except httpx.HTTPStatusError as exc:
                        raise ModelSubmissionError(
                            "downstream service returned an HTTP error",
                            status_code=exc.response.status_code,
                        ) from exc
                    except httpx.RequestError as exc:
                        raise ModelSubmissionError(
                            "downstream service request failed"
                        ) from exc
                    except ValueError as exc:
                        raise ModelSubmissionError(
                            "downstream service returned invalid JSON"
                        ) from exc

                    if not isinstance(res, dict):
                        raise ModelSubmissionError(
                            "downstream service returned a non-object response"
                        )

                    success = _parse_success(res.get("success"))
                    if success is None:
                        raise ModelSubmissionError(
                            "downstream service returned an invalid success flag",
                            code=res.get("code"),
                            backend_message=res.get("message"),
                        )
                    if not success:
                        raise ModelSubmissionError(
                            "downstream service rejected the submission",
                            success=False,
                            code=res.get("code"),
                            backend_message=res.get("message"),
                        )

                    data = res.get("data")
                    if not isinstance(data, dict):
                        raise ModelSubmissionError(
                            "downstream service returned invalid submission data",
                            success=True,
                            code=res.get("code"),
                            backend_message=res.get("message"),
                        )
                    project_id = data.get("project_id")
                    if not isinstance(project_id, str) or not project_id.strip():
                        raise ModelSubmissionError(
                            "downstream service response omitted project_id",
                            success=True,
                            code=res.get("code"),
                            backend_message=res.get("message"),
                        )
                    return project_id.strip()

                return model_function

            model_function = create_model_function(m_id, m_name)
            model_function.__name__ = m_name
            model_functions[m_name] = model_function

        return model_functions

    def __getattr__(self, name: str) -> Callable:
        if name in self.model_functions:
            return self.model_functions[name]
        raise AttributeError(f"No such model: {name}")
