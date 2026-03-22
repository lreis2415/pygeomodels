from typing import Any, Optional

import httpx

from auth_context import get_bearer_token


def get_required_bearer_token(access_token: Optional[str] = None) -> str:
    token = access_token or get_bearer_token()
    if token is None or str(token).strip() == "":
        raise ValueError("Missing Bearer token in MCP request")
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
