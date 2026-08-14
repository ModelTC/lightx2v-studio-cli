from __future__ import annotations

import json
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx

from lightx2v import __version__
from lightx2v.cli.config import CliConfig
from lightx2v.cli.update_check import UpdateChecker


class ApiError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class LightX2VClient:
    def __init__(self, config: CliConfig, *, timeout: float = 120.0, notify_updates: bool = True):
        self.config = config
        self._update_checker = UpdateChecker(current_version=__version__, enabled=notify_updates)
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": f"lightx2v-cli/{__version__}",
            },
        )

    def close(self) -> None:
        self._client.close()
        notice = self._update_checker.consume_notice()
        if notice:
            print(f"\n{notice}", file=sys.stderr)

    def __enter__(self) -> LightX2VClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(self, method: str, path: str, *, json: dict | None = None, params: dict | None = None) -> Any:
        last_error: ApiError | None = None
        for attempt in range(5):
            response = self._client.request(method, path, json=json, params=params)
            self._update_checker.observe_headers(response.headers)
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
        self._update_checker.observe_headers(response.headers)
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
        self._update_checker.observe_headers(response.headers)
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
                "User-Agent": f"lightx2v-cli/{__version__}",
            },
        ) as multipart_client:
            files = {"file": (path.name, audio, "application/octet-stream")}
            data = {"text": text} if text else None
            response = multipart_client.post(
                "/api/v1/voice/clone",
                files=files,
                data=data,
            )
        self._update_checker.observe_headers(response.headers)
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

    def get_workflow_inputs(
        self,
        workflow_id: str,
        *,
        mode: str = "full",
        node_ids: list[str] | None = None,
        include_upstream: bool = True,
    ) -> dict:
        params: dict[str, Any] = {
            "mode": mode,
            "include_upstream": "true" if include_upstream else "false",
        }
        if node_ids:
            params["node_ids"] = ",".join(node_ids)
        return self._request("GET", f"/api/v1/workflow/{workflow_id}/inputs", params=params)

    def create_workflow(self, body: dict) -> dict:
        return self._request("POST", "/api/v1/workflow/create", json=body)

    def start_workflow_run(self, workflow_id: str, body: dict) -> dict:
        return self._request("POST", f"/api/v1/workflow/{workflow_id}/runs", json=body)

    def list_workflow_runs(self, workflow_id: str, *, status: str | None = None) -> dict:
        params = {"status": status} if status else None
        return self._request("GET", f"/api/v1/workflow/{workflow_id}/runs", params=params)

    def get_workflow_run(self, workflow_id: str, run_id: str) -> dict:
        return self._request("GET", f"/api/v1/workflow/{workflow_id}/runs/{run_id}")

    def get_workflow_run_outputs(self, workflow_id: str, run_id: str) -> dict:
        return self._request("GET", f"/api/v1/workflow/{workflow_id}/runs/{run_id}/outputs")

    def stream_workflow_run(self, workflow_id: str, run_id: str) -> Iterator[dict[str, Any]]:
        path = f"/api/v1/workflow/{workflow_id}/runs/{run_id}/stream"
        with self._client.stream("GET", path, headers={"Accept": "text/event-stream"}) as response:
            self._update_checker.observe_headers(response.headers)
            if not response.is_success:
                response.read()
                raise self._parse_error(response)

            event_name = "message"
            data_lines: list[str] = []
            for line in response.iter_lines():
                if line == "":
                    if data_lines:
                        raw = "\n".join(data_lines)
                        try:
                            data: Any = json.loads(raw)
                        except json.JSONDecodeError:
                            data = raw
                        yield {"event": event_name, "data": data}
                    event_name = "message"
                    data_lines = []
                    continue
                if line.startswith("event:"):
                    event_name = line[6:].strip() or "message"
                elif line.startswith("data:"):
                    data_lines.append(line[5:].lstrip())

            if data_lines:
                raw = "\n".join(data_lines)
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    data = raw
                yield {"event": event_name, "data": data}

    def cancel_workflow_run(self, workflow_id: str, run_id: str) -> dict:
        return self._request("POST", f"/api/v1/workflow/{workflow_id}/runs/{run_id}/cancel", json={})

    def cancel_workflow_run_node(self, workflow_id: str, run_id: str, node_id: str) -> dict:
        return self._request(
            "POST",
            f"/api/v1/workflow/{workflow_id}/runs/{run_id}/cancel-node",
            json={"node_id": node_id},
        )
