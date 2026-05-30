from __future__ import annotations

import json
import mimetypes
import threading
import time
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .config import AppConfig
from .model import ModelService


ROOT_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT_DIR / "web"


class ScriptTunerHandler(BaseHTTPRequestHandler):
    model_service: ModelService
    config: AppConfig

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"server": "ok"})
            return
        if self.path == "/status":
            self._send_json(self.model_service.status())
            return
        if self.path == "/" or self.path == "/index.html":
            self._send_file(STATIC_DIR / "index.html")
            return

        static_path = STATIC_DIR / self.path.lstrip("/")
        if static_path.is_file() and static_path.resolve().is_relative_to(STATIC_DIR.resolve()):
            self._send_file(static_path)
            return

        self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path == "/token":
            try:
                payload = self._read_json()
                token = str(payload.get("token", ""))
                self._send_json(self.model_service.submit_token(token))
            except ValueError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except Exception as exc:
                self._send_json({"error": f"{type(exc).__name__}: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if self.path != "/tune":
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return

        try:
            payload = self._read_json()
            script = str(payload.get("script", ""))
            style = str(payload.get("style", "casual"))
            started = time.monotonic()
            tuned = self.model_service.tune(script=script, style=style)
            self._send_json(
                {
                    "tuned_script": tuned,
                    "style": style,
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                }
            )
        except ValueError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except RuntimeError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)
        except Exception as exc:
            self._send_json({"error": f"{type(exc).__name__}: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")

    def _read_json(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        body = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self._send_cors_headers()
        self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith("text/") else content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def make_server(config: AppConfig) -> ThreadingHTTPServer:
    service = ModelService(config)
    ScriptTunerHandler.model_service = service
    ScriptTunerHandler.config = config
    server = ThreadingHTTPServer((config.host, config.port), ScriptTunerHandler)
    service.start_loading()
    return server


def main(open_browser: bool = True) -> None:
    config = AppConfig()
    server = make_server(config)
    url = f"http://{config.host}:{config.port}/"
    print(f"Script-Tuner service is running at {url}")
    print("Keep this window open while using the service.")
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping Script-Tuner service...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
