from typing import Any, Optional

import httpx

from auth_context import get_bearer_token
from pygeomodels.config import parse_config


def get_required_bearer_token(access_token: Optional[str] = None) -> str:
    # First try the provided access_token or bearer token from request context
    token = access_token or get_bearer_token()

    # If no token from request, try test token from config (for local development)
    if not token or str(token).strip() == "":
        try:
            cfg = parse_config()
            token = cfg.test_bearer_token
        except Exception:
            token = ''

    if token is None or str(token).strip() == "":
        raise ValueError("Missing Bearer token in MCP request. Provide via Authorization header or configure test_bearer_token in local_config.ini")
    return str(token).strip()


def call_inner_api(
    method: str,
    host: str,
    path: str,
    json_body: Optional[dict[str, Any]] = None,
    access_token: Optional[str] = None,
) -> dict[str, Any]:
    token = get_required_bearer_token(access_token)
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{host}/{path.lstrip('/')}"

    with httpx.Client(timeout=30) as client:
        resp = client.request(
            method=method,
            url=url,
            json=json_body,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()
