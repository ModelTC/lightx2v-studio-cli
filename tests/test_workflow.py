import httpx

from lightx2v.cli.client import LightX2VClient
from lightx2v.cli.config import CliConfig
from lightx2v.cli.main import build_parser


def test_workflow_runtime_commands_are_registered():
    parser = build_parser()

    assert parser.parse_args(["workflow", "inputs", "wf-1"]).workflow_command == "inputs"
    assert parser.parse_args(["workflow", "runs", "wf-1"]).workflow_command == "runs"
    assert parser.parse_args(["workflow", "stream", "wf-1", "run-1"]).workflow_command == "stream"
    assert (
        parser.parse_args(["workflow", "cancel-node", "wf-1", "run-1", "node-1"]).workflow_command
        == "cancel-node"
    )


def test_workflow_runtime_client_builds_public_contract_requests():
    client = LightX2VClient(CliConfig(base_url="https://example.test", api_key="apikey_test"))
    calls = []

    def request(method, path, *, json=None, params=None):
        calls.append((method, path, json, params))
        return {}

    client._request = request
    try:
        client.get_workflow_inputs(
            "wf-1",
            mode="downstream",
            node_ids=["node-a", "node-b"],
            include_upstream=False,
        )
        client.list_workflow_runs("wf-1", status="running")
        client.cancel_workflow_run_node("wf-1", "run-1", "node-a")
    finally:
        client.close()

    assert calls == [
        (
            "GET",
            "/api/v1/workflow/wf-1/inputs",
            None,
            {"mode": "downstream", "include_upstream": "false", "node_ids": "node-a,node-b"},
        ),
        ("GET", "/api/v1/workflow/wf-1/runs", None, {"status": "running"}),
        (
            "POST",
            "/api/v1/workflow/wf-1/runs/run-1/cancel-node",
            {"node_id": "node-a"},
            None,
        ),
    ]


def test_workflow_stream_parses_sse_events():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/workflow/wf-1/runs/run-1/stream"
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text=(
                'event: run_status\ndata: {"status":"running"}\n\n'
                'event: run_outputs\ndata: {"pending":false,"outputs":[]}\n\n'
            ),
        )

    client = LightX2VClient(CliConfig(base_url="https://example.test", api_key="apikey_test"))
    client._client.close()
    client._client = httpx.Client(
        base_url="https://example.test",
        transport=httpx.MockTransport(handler),
        headers={"Authorization": "Bearer apikey_test"},
    )
    try:
        events = list(client.stream_workflow_run("wf-1", "run-1"))
    finally:
        client.close()

    assert events == [
        {"event": "run_status", "data": {"status": "running"}},
        {"event": "run_outputs", "data": {"pending": False, "outputs": []}},
    ]
