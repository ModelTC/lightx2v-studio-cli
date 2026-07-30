from __future__ import annotations

import time
from pathlib import Path
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

    def _request_bytes(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        timeout: float | None = None,
    ) -> tuple[bytes, str]:
        response = self._client.request(method, path, json=json, params=params, timeout=timeout)
        if not response.is_success:
            raise self._parse_error(response)
        return response.content, response.headers.get("content-type", "")

    @staticmethod
    def _parse_error(response: httpx.Response) -> ApiError:
        message = response.text
        try:
            payload = response.json()
            if isinstance(payload, dict) and payload.get("message"):
                message = str(payload["message"])
            elif isinstance(payload, dict) and payload.get("error"):
                message = str(payload["error"])
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

    def list_voices(self, *, version: str = "all", fields: str = "card") -> dict:
        return self._request("GET", "/api/v1/voices/list", params={"version": version, "fields": fields})

    def generate_tts(self, body: dict) -> tuple[bytes, str]:
        return self._request_bytes("POST", "/api/v1/tts/generate", json=body, timeout=180.0)

    def create_voice_clone(self, audio_path: str | Path, *, text: str = "") -> dict:
        path = Path(audio_path)
        with path.open("rb") as audio, httpx.Client(
            base_url=self.config.base_url,
            timeout=240.0,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Accept": "application/json",
            },
        ) as multipart_client:
            files = {"file": (path.name, audio, "application/octet-stream")}
            data = {"text": text} if text else None
            response = multipart_client.post(
                "/api/v1/voice/clone",
                files=files,
                data=data,
            )
        if response.is_success:
            return response.json()
        raise self._parse_error(response)

    def save_voice_clone(self, speaker_id: str, name: str) -> dict:
        return self._request("POST", "/api/v1/voice/clone/save", json={"speaker_id": speaker_id, "name": name})

    def list_voice_clones(self) -> dict:
        return self._request("GET", "/api/v1/voice/clone/list")

    def generate_voice_clone_tts(self, body: dict) -> tuple[bytes, str]:
        return self._request_bytes("POST", "/api/v1/voice/clone/tts", json=body, timeout=180.0)

    def delete_voice_clone(self, speaker_id: str) -> dict:
        return self._request("DELETE", f"/api/v1/voice/clone/{speaker_id}")

    def list_workflows(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        public: bool = False,
        search: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "public": "true" if public else "false",
        }
        if search:
            params["search"] = search
        return self._request("GET", "/api/v1/workflow/list", params=params)

    def get_workflow(self, workflow_id: str) -> dict:
        return self._request("GET", f"/api/v1/workflow/{workflow_id}")

    def create_workflow(self, body: dict) -> dict:
        return self._request("POST", "/api/v1/workflow/create", json=body)

    def start_workflow_run(self, workflow_id: str, body: dict) -> dict:
        return self._request("POST", f"/api/v1/workflow/{workflow_id}/runs", json=body)

    def get_workflow_run(self, workflow_id: str, run_id: str) -> dict:
        return self._request("GET", f"/api/v1/workflow/{workflow_id}/runs/{run_id}")

    def get_workflow_run_outputs(self, workflow_id: str, run_id: str) -> dict:
        return self._request("GET", f"/api/v1/workflow/{workflow_id}/runs/{run_id}/outputs")

    def cancel_workflow_run(self, workflow_id: str, run_id: str) -> dict:
        return self._request("POST", f"/api/v1/workflow/{workflow_id}/runs/{run_id}/cancel", json={})
