from __future__ import annotations

import time
from typing import Any

import httpx

from lightx2v.cli.config import CliConfig


class ApiError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class LightX2VClient:
    def __init__(self, config: CliConfig, *, timeout: float = 120.0):
        self.config = config
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> LightX2VClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(self, method: str, path: str, *, json: dict | None = None, params: dict | None = None) -> Any:
        last_error: ApiError | None = None
        for attempt in range(5):
            response = self._client.request(method, path, json=json, params=params)
            if response.status_code == 429 and attempt < 4:
                time.sleep(0.05 * (attempt + 1))
                continue
            if response.is_success:
                if not response.content:
                    return {}
                return response.json()
            last_error = self._parse_error(response)
            break
        assert last_error is not None
        raise last_error

    @staticmethod
    def _parse_error(response: httpx.Response) -> ApiError:
        message = response.text
        try:
            payload = response.json()
            if isinstance(payload, dict) and payload.get("message"):
                message = str(payload["message"])
        except Exception:
            pass
        return ApiError(response.status_code, message)

    def list_models(self) -> dict:
        return self._request("GET", "/api/v1/model/list")

    def quote(self, body: dict) -> dict:
        return self._request("POST", "/api/v1/billing/quote", json=body)

    def submit(self, body: dict) -> dict:
        return self._request("POST", "/api/v1/task/submit", json=body)

    def query(self, task_id: str) -> dict:
        return self._request("GET", "/api/v1/task/query", params={"task_id": task_id})

    def result_url(self, task_id: str, name: str) -> dict:
        return self._request("GET", "/api/v1/task/result_url", params={"task_id": task_id, "name": name})

    def list_tasks(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        status: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        return self._request("GET", "/api/v1/task/list", params=params)

    def cancel(self, task_id: str) -> dict:
        return self._request("POST", "/api/v1/task/cancel", json={"task_id": task_id})

    def resume(self, task_id: str) -> dict:
        return self._request("POST", "/api/v1/task/resume", json={"task_id": task_id})

    def delete(self, task_id: str) -> dict:
        return self._request("DELETE", "/api/v1/task/delete", params={"task_id": task_id})

    def download(self, url: str) -> bytes:
        response = self._client.get(url, follow_redirects=True)
        if not response.is_success:
            raise ApiError(response.status_code, response.text)
        return response.content
