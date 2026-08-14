import json
from datetime import datetime, timedelta, timezone

import httpx

from lightx2v.cli.client import LightX2VClient
from lightx2v.cli.config import CliConfig
from lightx2v.cli.main import build_parser
from lightx2v.cli.update_check import UpdateChecker, compare_versions


def test_compare_versions_handles_semver_core_and_prerelease():
    assert compare_versions("0.2.0", "0.1.9") > 0
    assert compare_versions("1.0.0", "1.0.0") == 0
    assert compare_versions("1.0.0-rc.1", "1.0.0") < 0


def test_update_checker_emits_once_per_day_and_marks_minimum_version(tmp_path):
    cache = tmp_path / "update-check.json"
    now = datetime(2026, 8, 14, tzinfo=timezone.utc)
    checker = UpdateChecker(current_version="0.1.0", cache_path=cache, now=lambda: now)
    checker.observe_headers(
        {
            "X-LightX2V-CLI-Latest-Version": "0.2.0",
            "X-LightX2V-CLI-Min-Version": "0.1.5",
            "X-LightX2V-CLI-Update-URL": "https://example.test/install.sh",
        }
    )

    notice = checker.consume_notice()
    assert "may be incompatible" in notice
    assert "lightx2v update" in notice
    assert checker.consume_notice() is None

    next_process = UpdateChecker(current_version="0.1.0", cache_path=cache, now=lambda: now + timedelta(hours=1))
    next_process.observe_headers({"X-LightX2V-CLI-Latest-Version": "0.2.0"})
    assert next_process.consume_notice() is None

    next_day = UpdateChecker(current_version="0.1.0", cache_path=cache, now=lambda: now + timedelta(days=1, seconds=1))
    next_day.observe_headers({"X-LightX2V-CLI-Latest-Version": "0.2.0"})
    assert "New LightX2V CLI version available" in next_day.consume_notice()

    state = json.loads(cache.read_text(encoding="utf-8"))
    assert state["latest_version"] == "0.2.0"


def test_client_sends_version_and_prints_server_update_notice_once(tmp_path, capsys):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["user-agent"] == "lightx2v-cli/0.2.0"
        return httpx.Response(
            200,
            headers={"X-LightX2V-CLI-Latest-Version": "0.3.0"},
            json={"models": []},
        )

    client = LightX2VClient(CliConfig(base_url="https://example.test", api_key="apikey_test"))
    client._client.close()
    client._client = httpx.Client(
        base_url="https://example.test",
        transport=httpx.MockTransport(handler),
        headers={"User-Agent": "lightx2v-cli/0.2.0"},
    )
    client._update_checker.cache_path = tmp_path / "update-check.json"

    with client:
        client.list_models()

    assert "New LightX2V CLI version available: 0.3.0" in capsys.readouterr().err


def test_disabled_update_checker_stays_silent(tmp_path):
    checker = UpdateChecker(
        current_version="0.2.0",
        cache_path=tmp_path / "update-check.json",
        enabled=False,
    )
    checker.observe_headers({"X-LightX2V-CLI-Latest-Version": "0.3.0"})

    assert checker.consume_notice() is None
    assert not checker.cache_path.exists()


def test_root_parser_exposes_version_and_update_command(capsys):
    parser = build_parser()
    assert parser.parse_args(["update"]).command == "update"

    try:
        parser.parse_args(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("--version should terminate parsing")
    assert "lightx2v 0.2.0" in capsys.readouterr().out
