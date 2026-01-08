import requests
from typing import Optional, Any
from dataclasses import dataclass
from urllib.parse import urljoin


@dataclass
class APIResponse:
    status_code: int
    json_data: Optional[dict]
    headers: dict
    elapsed_ms: float
    raw_response: requests.Response

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def get(self, key: str, default: Any = None) -> Any:
        if self.json_data:
            return self.json_data.get(key, default)
        return default


class APIClient:

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self._token: Optional[str] = None

    def set_auth_token(self, token: str) -> None:
        self._token = token
        self.session.headers["Authorization"] = f"Bearer {token}"

    def clear_auth(self) -> None:
        self._token = None
        self.session.headers.pop("Authorization", None)

    def _url(self, endpoint: str) -> str:
        return urljoin(self.base_url, endpoint)

    def _request(self, method: str, endpoint: str, **kwargs) -> APIResponse:
        url = self._url(endpoint)
        kwargs.setdefault("timeout", self.timeout)

        resp = self.session.request(method, url, **kwargs)

        try:
            data = resp.json()
        except ValueError:
            data = None

        return APIResponse(
            status_code=resp.status_code,
            json_data=data,
            headers=dict(resp.headers),
            elapsed_ms=resp.elapsed.total_seconds() * 1000,
            raw_response=resp
        )

    def get(self, endpoint: str, params: dict = None) -> APIResponse:
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, json: dict = None, data: dict = None) -> APIResponse:
        return self._request("POST", endpoint, json=json, data=data)

    def put(self, endpoint: str, json: dict = None) -> APIResponse:
        return self._request("PUT", endpoint, json=json)

    def patch(self, endpoint: str, json: dict = None) -> APIResponse:
        return self._request("PATCH", endpoint, json=json)

    def delete(self, endpoint: str) -> APIResponse:
        return self._request("DELETE", endpoint)


class UserServiceClient(APIClient):
    """client for user api endpoints"""

    def create_user(self, email: str, name: str, password: str) -> APIResponse:
        return self.post("/users", json={
            "email": email,
            "name": name,
            "password": password
        })

    def get_user(self, user_id: str) -> APIResponse:
        return self.get(f"/users/{user_id}")

    def update_user(self, user_id: str, **fields) -> APIResponse:
        return self.patch(f"/users/{user_id}", json=fields)

    def delete_user(self, user_id: str) -> APIResponse:
        return self.delete(f"/users/{user_id}")

    def list_users(self, page: int = 1, limit: int = 20) -> APIResponse:
        return self.get("/users", params={"page": page, "limit": limit})

    def login(self, email: str, password: str) -> APIResponse:
        resp = self.post("/auth/login", json={
            "email": email,
            "password": password
        })

        # auto set token if login successful
        if resp.is_success:
            token = resp.get("access_token")
            if token:
                self.set_auth_token(token)

        return resp
