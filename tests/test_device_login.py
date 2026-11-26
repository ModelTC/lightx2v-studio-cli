import json

from lightx2v.cli.commands import login
from lightx2v.cli import config
from lightx2v.cli.main import main


def test_legacy_login_uses_hidden_prompt_and_atomic_private_file(tmp_path, monkeypatch, capsys):
    profile = tmp_path / "profile"
    monkeypatch.setattr(config, "CONFIG_PATH", profile / "config.json")
    monkeypatch.setattr(login.getpass, "getpass", lambda _: "apikey_fixture_secret")
    assert main(["login", "--api-key", "--json"]) == 0
    shown = capsys.readouterr().out
    assert json.loads(shown)["status"] == "configured"
    assert "apikey_fixture_secret" not in shown
    assert json.loads(config.CONFIG_PATH.read_text())["api_key"] == "apikey_fixture_secret"
    assert config.CONFIG_PATH.stat().st_mode & 0o777 == 0o600


def test_browser_login_rejects_credential_override_before_sending_request(tmp_path, monkeypatch, capsys):
    path = tmp_path / "config.json"
    monkeypatch.setattr(config, "CONFIG_PATH", path)
    monkeypatch.setenv("LIGHTX2V_API_KEY", "apikey_fixture_override")
    assert main(["login", "--headless", "--json"]) == 1
    output = capsys.readouterr().out
    assert "overrides" in json.loads(output)["message"]
    assert "apikey_fixture_override" not in output
    assert not path.exists()

