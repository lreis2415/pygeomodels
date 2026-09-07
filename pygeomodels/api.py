from typing import Any, Optional

from mcp_service.inner_api import call_inner_api


def restapi_get(
    host: str, method: str, access_token: Optional[str] = None
) -> Optional[dict[str, Any]]:
    # For example,
    #   host = "http://modelmanager:7504"
    #   method = "mbms/v1/model-manager/general-models/catalog"
    try:
        return call_inner_api("GET", host, method, access_token=access_token)
    except Exception:
        print("Get API (%s/%s) failed!" % (host, method))
        return None


def restapi_post(
    host: str,
    method: str,
    body: dict[str, Any],
    access_token: Optional[str] = None,
    raise_on_error: bool = False,
) -> Optional[dict[str, Any]]:
    try:
        return call_inner_api(
            "POST", host, method, json_body=body, access_token=access_token
        )
    except Exception:
        if raise_on_error:
            raise
        print("POST API (%s/%s) failed!" % (host, method))
        return None


if __name__ == "__main__":
    pass
