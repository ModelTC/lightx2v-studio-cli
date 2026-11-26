from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import time
import webbrowser
from urllib.parse import urlsplit

import httpx

from lightx2v.cli.config import CONFIG_DIR, DEFAULT_BASE_URL, load_config_file, save_config_file, write_private_json


class LoginError(Exception):
    pass


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("login", help="Authorize the CLI in your browser")
    parser.add_argument("--base-url", help="LightX2V API origin")
    parser.add_argument("--language", choices=("zh", "en"), default="zh")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--api-key", action="store_true", help="Enter a legacy API key through a hidden prompt")
    mode.add_argument("--headless", action="store_true", help="Start authorization and return without waiting")
    mode.add_argument("--resume", action="store_true", help="Check the saved authorization once")
    parser.add_argument("--json", action="store_true", help="Print only public login status as JSON")
    parser.set_defaults(handler=handle)


def emit(args, data):
    if args.json:
        print(json.dumps(data, ensure_ascii=False))
    elif "verification_uri" in data:
        print(f"Open {data['verification_uri']} and confirm code {data['user_code']}.", flush=True)
    elif data["status"] == "connected":
        print(f"Connected to {data['base_url']} as {data.get('username') or data.get('user_id')}.")
    else:
        print(data.get("message", data["status"]))


def read_response(response):
    if response.status_code in (404, 405):
        raise LoginError("This server does not support browser login. Use lightx2v login --api-key.")
    try:
        data = response.json()
    except ValueError:
        raise LoginError("The server returned an invalid login response.") from None
    if not isinstance(data, dict):
        raise LoginError("The server returned an invalid login response.")
    if not response.is_success and not isinstance(data.get("error"), str):
        raise LoginError("Login request failed. Check the server and try again.")
    return data


def origin(value, *, allow_local_http):
    if not isinstance(value, str):
        raise LoginError("Missing LightX2V server URL.")
    parts = urlsplit(value)
    local = parts.hostname in {"localhost", "127.0.0.1", "::1"}
    if (not parts.hostname or parts.username or parts.password or parts.path not in ("", "/")
            or parts.query or parts.fragment
            or not (parts.scheme == "https" or allow_local_http and local and parts.scheme == "http")):
        raise LoginError("Use an HTTPS LightX2V origin, or HTTP on localhost for development.")
    return f"{parts.scheme}://{parts.netloc.lower()}"


def pending_path(base):
    return CONFIG_DIR / ("device-login-" + hashlib.sha256(base.encode()).hexdigest() + ".json")


def public_status(state, pending, **fields):
    return {"status": state, "verification_uri": pending["verification_uri"],
            "user_code": pending["user_code"], "expires_at": int(pending["expires_at"]), **fields}


def browser_login(args, base):
    path = pending_path(base)
    with httpx.Client(base_url=base, timeout=12, follow_redirects=False) as http:
        if args.resume:
            if not path.is_file():
                raise LoginError("No pending login for this server. Start with lightx2v login --headless.")
            pending = json.loads(path.read_text(encoding="utf-8"))
        else:
            grant = read_response(http.post("/api/v1/cli/device/start", json={"language": args.language}))
            if "error" in grant:
                raise LoginError("Unable to start authorization. Try again in a minute.")
            url = urlsplit(grant["verification_uri"])
            if (origin(f"{url.scheme}://{url.netloc}", allow_local_http=True) != base
                    or url.path not in ("/cli/authorize", "/en/cli/authorize")
                    or url.query or url.fragment):
                raise LoginError("The server returned an unexpected authorization URL.")
            pending = {key: grant[key] for key in ("device_code", "verification_uri", "user_code", "interval")}
            pending.update(expires_at=time.time() + int(grant["expires_in"]), next_poll=time.time())
            write_private_json(path, pending)
            if args.headless:
                emit(args, public_status("authorization_pending", pending, retry_after=pending["interval"]))
                return 0
            if not args.json:
                emit(args, public_status("authorization_pending", pending))
            try:
                webbrowser.open(pending["verification_uri"])
            except (OSError, webbrowser.Error):
                pass

        while time.time() < pending["expires_at"]:
            delay = max(0, pending["next_poll"] - time.time())
            if args.resume and delay > 0:
                emit(args, public_status("authorization_pending", pending, retry_after=max(1, int(delay + 0.99))))
                return 3
            if delay:
                time.sleep(min(delay, max(0, pending["expires_at"] - time.time())))
                continue
            data = read_response(http.post("/api/v1/cli/device/token", json={"device_code": pending["device_code"]}))
            error = data.get("error")
            if error in {"authorization_pending", "slow_down"}:
                delay = max(5, int(data.get("interval", pending["interval"])))
                pending["next_poll"] = time.time() + delay
                write_private_json(path, pending)
                if args.resume:
                    emit(args, public_status(error, pending, retry_after=delay))
                    return 3
                continue
            if error in {"access_denied", "expired_token"}:
                path.unlink(missing_ok=True)
                emit(args, {"status": error})
                return 1
            key = data.get("api_key")
            if not isinstance(key, str) or not key:
                raise LoginError("Could not claim the login. Retry with lightx2v login --resume.")
            account = read_response(http.get("/api/v1/cli/session", headers={"Authorization": f"Bearer {key}"}))
            if not account.get("user_id"):
                raise LoginError("Could not verify the new login. Retry with lightx2v login --resume.")
            save_config_file(base, key)
            path.unlink(missing_ok=True)
            emit(args, {"status": "connected", "base_url": base, "user_id": account["user_id"],
                        "username": account.get("username"), "expires_at": data.get("expires_at")})
            return 0
        path.unlink(missing_ok=True)
        emit(args, {"status": "expired_token"})
        return 1


def handle(args: argparse.Namespace) -> int:
    try:
        configured = next((os.environ[name].strip() for name in
                           ("LIGHTX2V_BASE_URL", "LIGHTX2V_CLOUD_URL", "API_BASE_URL")
                           if os.environ.get(name, "").strip()), None)
        base = args.base_url or configured or load_config_file().get("base_url") or DEFAULT_BASE_URL
        if args.api_key:
            # Keep the legacy custom deployment URL behavior for manual credentials.
            key = getpass.getpass("API Key: ").strip()
            if not key:
                raise LoginError("API key is required.")
            save_config_file(base, key)
            emit(args, {"status": "configured", "base_url": base})
            return 0
        base = origin(base, allow_local_http=True)
        if any(os.environ.get(name, "").strip() for name in ("LIGHTX2V_API_KEY", "LIGHTX2V_CLOUD_API_KEY")):
            raise LoginError("An API key environment variable overrides CLI login. Unset it before browser authorization.")
        if configured and origin(configured, allow_local_http=True) != base:
            raise LoginError("The environment selects a different server. Update the environment before browser authorization.")
        return browser_login(args, base)
    except KeyboardInterrupt:
        emit(args, {"status": "interrupted", "message": "Waiting stopped. Use lightx2v login --resume to continue."})
        return 130
    except LoginError as exc:
        emit(args, {"status": "error", "message": str(exc)})
        return 1
    except (httpx.HTTPError, OSError, ValueError, KeyError, TypeError):
        emit(args, {"status": "error",
                    "message": "Authorization could not be completed. Retry with lightx2v login --resume."})
        return 1
