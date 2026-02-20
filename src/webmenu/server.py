import ipaddress
import json
import mimetypes
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse
import re

from src.utils.debug_logger import log_print


ALLOWED_MODES = {"Normal", "Silent", "NCAF", "WindMouse", "Bezier"}
ALLOWED_AIM_TYPES = {"head", "body", "nearest"}
ALLOWED_TRIGGER_TYPES = {"current", "rgb"}
ALLOWED_CAPTURE_MODES = {"NDI", "UDP", "CaptureCard", "MSS"}
ALLOWED_COLORS = {"purple", "yellow", "red", "custom"}


class WebMenuServer:
    def __init__(self, config, tracker, capture_service, version_provider: Callable[[], str] | None = None):
        self.config = config
        self.tracker = tracker
        self.capture_service = capture_service
        self.version_provider = version_provider
        self._lock = threading.RLock()
        self._server = None
        self._thread = None
        self._base_dir = Path(__file__).resolve().parents[2]
        self._web_ui_dir = self._base_dir / "web_ui"

    def start(self):
        with self._lock:
            if self._server is not None:
                return

            handler_cls = self._build_handler()
            self._server = ThreadingHTTPServer(
                (str(self.config.webmenu_host), int(self.config.webmenu_port)),
                handler_cls,
            )
            self._thread = threading.Thread(target=self._server.serve_forever, daemon=True, name="WebMenuServer")
            self._thread.start()
            log_print(f"[WebMenu] Running at http://{self.config.webmenu_host}:{self.config.webmenu_port}")

    def stop(self):
        with self._lock:
            if self._server is None:
                return
            server = self._server
            thread = self._thread
            self._server = None
            self._thread = None
        try:
            server.shutdown()
            server.server_close()
            if thread:
                thread.join(timeout=1.0)
            log_print("[WebMenu] Stopped")
        except Exception as exc:
            log_print(f"[WebMenu] Stop error: {exc}")

    def get_urls(self):
        import socket

        host = str(self.config.webmenu_host)
        port = int(self.config.webmenu_port)
        urls = []
        if host in ("0.0.0.0", "::"):
            urls.append(f"http://127.0.0.1:{port}")
            try:
                for entry in socket.getaddrinfo(socket.gethostname(), None):
                    ip = entry[4][0]
                    if "." in ip and not ip.startswith("127."):
                        urls.append(f"http://{ip}:{port}")
            except Exception:
                pass
        else:
            urls.append(f"http://{host}:{port}")

        seen = set()
        deduped = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                deduped.append(url)
        return deduped

    def _build_handler(self):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_OPTIONS(self):
                if not self._allow_client():
                    self._forbidden()
                    return
                self.send_response(HTTPStatus.NO_CONTENT)
                self._send_cors_headers()
                self.end_headers()

            def do_GET(self):
                if not self._allow_client():
                    self._forbidden()
                    return
                parsed = urlparse(self.path)
                path = parsed.path
                if path == "/api/v1/health":
                    self._json(HTTPStatus.OK, {"ok": True})
                    return
                if path == "/api/v1/meta":
                    self._json(
                        HTTPStatus.OK,
                        {
                            "app": "CVM colorBot",
                            "version": outer._get_version(),
                            "poll_ms": int(getattr(outer.config, "webmenu_poll_ms", 750)),
                        },
                    )
                    return
                if path == "/api/v1/state/main-aimbot":
                    self._json(HTTPStatus.OK, outer._build_main_aimbot_state())
                    return
                if path == "/api/v1/state/sec-aimbot":
                    self._json(HTTPStatus.OK, outer._build_sec_aimbot_state())
                    return
                if path == "/api/v1/state/trigger":
                    self._json(HTTPStatus.OK, outer._build_trigger_state())
                    return
                if path == "/api/v1/state/rcs":
                    self._json(HTTPStatus.OK, outer._build_rcs_state())
                    return
                if path == "/api/v1/state/general":
                    self._json(HTTPStatus.OK, outer._build_general_state())
                    return
                if path == "/api/v1/configs":
                    self._json(HTTPStatus.OK, {"configs": outer._list_configs()})
                    return

                if path == "/":
                    return self._serve_static("index.html")
                return self._serve_static(path.lstrip("/"))

            def do_PATCH(self):
                if not self._allow_client():
                    self._forbidden()
                    return
                parsed = urlparse(self.path)
                if parsed.path == "/api/v1/state/main-aimbot":
                    payload = self._read_json()
                    if payload is None:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
                        return
                    ok, err = outer._patch_main_aimbot(payload)
                    if not ok:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "validation_error", "message": err})
                        return
                    self._json(HTTPStatus.OK, outer._build_main_aimbot_state())
                    return
                if parsed.path == "/api/v1/state/sec-aimbot":
                    payload = self._read_json()
                    if payload is None:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
                        return
                    ok, err = outer._patch_sec_aimbot(payload)
                    if not ok:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "validation_error", "message": err})
                        return
                    self._json(HTTPStatus.OK, outer._build_sec_aimbot_state())
                    return
                if parsed.path == "/api/v1/state/trigger":
                    payload = self._read_json()
                    if payload is None:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
                        return
                    ok, err = outer._patch_trigger(payload)
                    if not ok:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "validation_error", "message": err})
                        return
                    self._json(HTTPStatus.OK, outer._build_trigger_state())
                    return
                if parsed.path == "/api/v1/state/rcs":
                    payload = self._read_json()
                    if payload is None:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
                        return
                    ok, err = outer._patch_rcs(payload)
                    if not ok:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "validation_error", "message": err})
                        return
                    self._json(HTTPStatus.OK, outer._build_rcs_state())
                    return
                if parsed.path == "/api/v1/state/general":
                    payload = self._read_json()
                    if payload is None:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
                        return
                    ok, err = outer._patch_general(payload)
                    if not ok:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "validation_error", "message": err})
                        return
                    self._json(HTTPStatus.OK, outer._build_general_state())
                    return
                else:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                    return

            def do_POST(self):
                if not self._allow_client():
                    self._forbidden()
                    return
                parsed = urlparse(self.path)
                if parsed.path == "/api/v1/actions/save-config":
                    try:
                        outer.config.save_to_file()
                        self._json(HTTPStatus.OK, {"ok": True})
                    except Exception as exc:
                        self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "save_failed", "message": str(exc)})
                    return
                if parsed.path == "/api/v1/configs/load":
                    payload = self._read_json()
                    if payload is None:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
                        return
                    name = str(payload.get("name", "")).strip()
                    ok, err = outer._load_named_config(name)
                    if not ok:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "load_failed", "message": err})
                        return
                    self._json(HTTPStatus.OK, {"ok": True, "name": name})
                    return
                if parsed.path == "/api/v1/configs/save-new":
                    payload = self._read_json()
                    if payload is None:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
                        return
                    name = str(payload.get("name", "")).strip()
                    ok, err, saved_name = outer._save_new_named_config(name)
                    if not ok:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "save_failed", "message": err})
                        return
                    self._json(HTTPStatus.OK, {"ok": True, "name": saved_name})
                    return
                self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

            def _allow_client(self):
                if not bool(getattr(outer.config, "webmenu_allow_lan_only", True)):
                    return True
                return outer._is_client_allowed(self.client_address[0])

            def _forbidden(self):
                self._json(HTTPStatus.FORBIDDEN, {"error": "forbidden"})

            def _serve_static(self, relative_path: str):
                target = (outer._web_ui_dir / relative_path).resolve()
                if not str(target).startswith(str(outer._web_ui_dir.resolve())):
                    return self._json(HTTPStatus.FORBIDDEN, {"error": "forbidden"})

                if not target.exists() or not target.is_file():
                    # SPA fallback to index for non-api routes.
                    fallback = outer._web_ui_dir / "index.html"
                    if fallback.exists():
                        target = fallback
                    else:
                        return self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

                ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
                try:
                    body = target.read_bytes()
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(len(body)))
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(body)
                except Exception as exc:
                    self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "serve_failed", "message": str(exc)})

            def _read_json(self):
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    return None
                if length <= 0:
                    return {}
                raw = self.rfile.read(length)
                try:
                    return json.loads(raw.decode("utf-8"))
                except Exception:
                    return None

            def _json(self, status: HTTPStatus, payload):
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(int(status))
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(body)

            def _send_cors_headers(self):
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET,POST,PATCH,OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")

            def log_message(self, format, *args):
                # keep console clean; use app logger for explicit events only
                return

        return Handler

    def _get_version(self):
        try:
            if callable(self.version_provider):
                return str(self.version_provider())
            if self.version_provider is not None and hasattr(self.version_provider, "get_current_version"):
                return str(self.version_provider.get_current_version())
        except Exception:
            pass
        return "unknown"

    def _build_connected_summary(self):
        capture_connected = False
        mouse_connected = False
        mode = str(getattr(self.config, "capture_mode", "NDI"))
        try:
            if self.capture_service is not None and hasattr(self.capture_service, "is_connected"):
                capture_connected = bool(self.capture_service.is_connected())
        except Exception:
            capture_connected = False
        try:
            from src.utils import mouse as mouse_backend

            mouse_connected = bool(getattr(mouse_backend, "is_connected", False))
        except Exception:
            mouse_connected = False
        return {
            "overall": bool(capture_connected or mouse_connected),
            "capture": bool(capture_connected),
            "mouse": bool(mouse_connected),
            "capture_mode": mode,
        }

    @staticmethod
    def is_lan_or_loopback_ip(ip: str):
        try:
            addr = ipaddress.ip_address(ip)
            return bool(addr.is_loopback or addr.is_private)
        except ValueError:
            return False

    def _is_client_allowed(self, ip: str):
        return self.is_lan_or_loopback_ip(ip)

    def _build_main_aimbot_state(self):
        with self._lock:
            return {
                "enableaim": bool(getattr(self.config, "enableaim", True)),
                "mode": str(getattr(self.config, "mode", "Normal")),
                "fovsize": float(getattr(self.config, "fovsize", 100)),
                "normal_x_speed": float(getattr(self.config, "normal_x_speed", 3)),
                "normal_y_speed": float(getattr(self.config, "normal_y_speed", 3)),
                "normalsmooth": float(getattr(self.config, "normalsmooth", 30)),
                "aim_type": str(getattr(self.config, "aim_type", "head")),
                "ads_fov_enabled": bool(getattr(self.config, "ads_fov_enabled", False)),
                "ads_fovsize": float(getattr(self.config, "ads_fovsize", getattr(self.config, "fovsize", 100))),
                "connected": self._build_connected_summary(),
                "version": self._get_version(),
            }

    def _build_sec_aimbot_state(self):
        with self._lock:
            return {
                "enableaim_sec": bool(getattr(self.config, "enableaim_sec", False)),
                "mode_sec": str(getattr(self.config, "mode_sec", "Normal")),
                "fovsize_sec": float(getattr(self.config, "fovsize_sec", 150)),
                "normal_x_speed_sec": float(getattr(self.config, "normal_x_speed_sec", 2)),
                "normal_y_speed_sec": float(getattr(self.config, "normal_y_speed_sec", 2)),
                "normalsmooth_sec": float(getattr(self.config, "normalsmooth_sec", 20)),
                "aim_type_sec": str(getattr(self.config, "aim_type_sec", "head")),
                "ads_fov_enabled_sec": bool(getattr(self.config, "ads_fov_enabled_sec", False)),
                "ads_fovsize_sec": float(getattr(self.config, "ads_fovsize_sec", getattr(self.config, "fovsize_sec", 150))),
                "connected": self._build_connected_summary(),
                "version": self._get_version(),
            }

    def _build_trigger_state(self):
        with self._lock:
            return {
                "enabletb": bool(getattr(self.config, "enabletb", False)),
                "trigger_type": str(getattr(self.config, "trigger_type", "current")),
                "tbfovsize": float(getattr(self.config, "tbfovsize", 5)),
                "tbdelay_min": float(getattr(self.config, "tbdelay_min", 0.08)),
                "tbdelay_max": float(getattr(self.config, "tbdelay_max", 0.15)),
                "trigger_roi_size": int(getattr(self.config, "trigger_roi_size", 8)),
                "trigger_min_pixels": int(getattr(self.config, "trigger_min_pixels", 4)),
                "trigger_min_ratio": float(getattr(self.config, "trigger_min_ratio", 0.03)),
                "trigger_ads_fov_enabled": bool(getattr(self.config, "trigger_ads_fov_enabled", False)),
                "trigger_ads_fovsize": float(getattr(self.config, "trigger_ads_fovsize", 5)),
                "connected": self._build_connected_summary(),
                "version": self._get_version(),
            }

    def _build_rcs_state(self):
        with self._lock:
            return {
                "enablercs": bool(getattr(self.config, "enablercs", False)),
                "rcs_pull_speed": int(getattr(self.config, "rcs_pull_speed", 10)),
                "rcs_activation_delay": int(getattr(self.config, "rcs_activation_delay", 100)),
                "rcs_rapid_click_threshold": int(getattr(self.config, "rcs_rapid_click_threshold", 200)),
                "rcs_release_y_enabled": bool(getattr(self.config, "rcs_release_y_enabled", False)),
                "rcs_release_y_duration": float(getattr(self.config, "rcs_release_y_duration", 1.0)),
                "connected": self._build_connected_summary(),
                "version": self._get_version(),
            }

    def _build_general_state(self):
        with self._lock:
            return {
                "color": str(getattr(self.config, "color", "purple")),
                "capture_mode": str(getattr(self.config, "capture_mode", "NDI")),
                "target_fps": int(getattr(self.config, "target_fps", 80)),
                "connected": self._build_connected_summary(),
                "version": self._get_version(),
            }

    def _patch_main_aimbot(self, payload):
        if not isinstance(payload, dict):
            return False, "payload must be an object"

        with self._lock:
            if "enableaim" in payload:
                self.config.enableaim = bool(payload["enableaim"])
                if hasattr(self.tracker, "enableaim"):
                    self.tracker.enableaim = self.config.enableaim

            if "mode" in payload:
                mode = str(payload["mode"])
                if mode not in ALLOWED_MODES:
                    return False, f"mode must be one of {sorted(ALLOWED_MODES)}"
                self.config.mode = mode
                if hasattr(self.tracker, "mode"):
                    self.tracker.mode = mode

            if "fovsize" in payload:
                try:
                    value = float(payload["fovsize"])
                except Exception:
                    return False, "fovsize must be a number"
                if value < 1 or value > 1000:
                    return False, "fovsize must be between 1 and 1000"
                self.config.fovsize = value
                if hasattr(self.tracker, "fovsize"):
                    self.tracker.fovsize = value

            if "normal_x_speed" in payload:
                try:
                    value = float(payload["normal_x_speed"])
                except Exception:
                    return False, "normal_x_speed must be a number"
                if value < 0.1 or value > 2000:
                    return False, "normal_x_speed must be between 0.1 and 2000"
                self.config.normal_x_speed = value
                if hasattr(self.tracker, "normal_x_speed"):
                    self.tracker.normal_x_speed = value

            if "normal_y_speed" in payload:
                try:
                    value = float(payload["normal_y_speed"])
                except Exception:
                    return False, "normal_y_speed must be a number"
                if value < 0.1 or value > 2000:
                    return False, "normal_y_speed must be between 0.1 and 2000"
                self.config.normal_y_speed = value
                if hasattr(self.tracker, "normal_y_speed"):
                    self.tracker.normal_y_speed = value

            if "normalsmooth" in payload:
                try:
                    value = float(payload["normalsmooth"])
                except Exception:
                    return False, "normalsmooth must be a number"
                if value < 1 or value > 30:
                    return False, "normalsmooth must be between 1 and 30"
                self.config.normalsmooth = value
                if hasattr(self.tracker, "normalsmooth"):
                    self.tracker.normalsmooth = value

            if "aim_type" in payload:
                aim_type = str(payload["aim_type"]).lower()
                if aim_type not in ALLOWED_AIM_TYPES:
                    return False, f"aim_type must be one of {sorted(ALLOWED_AIM_TYPES)}"
                self.config.aim_type = aim_type
                if hasattr(self.tracker, "aim_type"):
                    self.tracker.aim_type = aim_type

            if "ads_fov_enabled" in payload:
                self.config.ads_fov_enabled = bool(payload["ads_fov_enabled"])
                if hasattr(self.tracker, "ads_fov_enabled"):
                    self.tracker.ads_fov_enabled = self.config.ads_fov_enabled

            if "ads_fovsize" in payload:
                try:
                    value = float(payload["ads_fovsize"])
                except Exception:
                    return False, "ads_fovsize must be a number"
                if value < 1 or value > 1000:
                    return False, "ads_fovsize must be between 1 and 1000"
                self.config.ads_fovsize = value
                if hasattr(self.tracker, "ads_fovsize"):
                    self.tracker.ads_fovsize = value

        return True, None

    def _patch_sec_aimbot(self, payload):
        if not isinstance(payload, dict):
            return False, "payload must be an object"
        with self._lock:
            if "enableaim_sec" in payload:
                self.config.enableaim_sec = bool(payload["enableaim_sec"])
                if hasattr(self.tracker, "enableaim_sec"):
                    self.tracker.enableaim_sec = self.config.enableaim_sec

            if "mode_sec" in payload:
                mode = str(payload["mode_sec"])
                if mode not in ALLOWED_MODES:
                    return False, f"mode_sec must be one of {sorted(ALLOWED_MODES)}"
                self.config.mode_sec = mode
                if hasattr(self.tracker, "mode_sec"):
                    self.tracker.mode_sec = mode

            if "fovsize_sec" in payload:
                try:
                    value = float(payload["fovsize_sec"])
                except Exception:
                    return False, "fovsize_sec must be a number"
                if value < 1 or value > 1000:
                    return False, "fovsize_sec must be between 1 and 1000"
                self.config.fovsize_sec = value
                if hasattr(self.tracker, "fovsize_sec"):
                    self.tracker.fovsize_sec = value

            if "normal_x_speed_sec" in payload:
                try:
                    value = float(payload["normal_x_speed_sec"])
                except Exception:
                    return False, "normal_x_speed_sec must be a number"
                if value < 0.1 or value > 2000:
                    return False, "normal_x_speed_sec must be between 0.1 and 2000"
                self.config.normal_x_speed_sec = value
                if hasattr(self.tracker, "normal_x_speed_sec"):
                    self.tracker.normal_x_speed_sec = value

            if "normal_y_speed_sec" in payload:
                try:
                    value = float(payload["normal_y_speed_sec"])
                except Exception:
                    return False, "normal_y_speed_sec must be a number"
                if value < 0.1 or value > 2000:
                    return False, "normal_y_speed_sec must be between 0.1 and 2000"
                self.config.normal_y_speed_sec = value
                if hasattr(self.tracker, "normal_y_speed_sec"):
                    self.tracker.normal_y_speed_sec = value

            if "normalsmooth_sec" in payload:
                try:
                    value = float(payload["normalsmooth_sec"])
                except Exception:
                    return False, "normalsmooth_sec must be a number"
                if value < 1 or value > 30:
                    return False, "normalsmooth_sec must be between 1 and 30"
                self.config.normalsmooth_sec = value
                if hasattr(self.tracker, "normalsmooth_sec"):
                    self.tracker.normalsmooth_sec = value

            if "aim_type_sec" in payload:
                aim_type = str(payload["aim_type_sec"]).lower()
                if aim_type not in ALLOWED_AIM_TYPES:
                    return False, f"aim_type_sec must be one of {sorted(ALLOWED_AIM_TYPES)}"
                self.config.aim_type_sec = aim_type
                if hasattr(self.tracker, "aim_type_sec"):
                    self.tracker.aim_type_sec = aim_type

            if "ads_fov_enabled_sec" in payload:
                self.config.ads_fov_enabled_sec = bool(payload["ads_fov_enabled_sec"])
                if hasattr(self.tracker, "ads_fov_enabled_sec"):
                    self.tracker.ads_fov_enabled_sec = self.config.ads_fov_enabled_sec

            if "ads_fovsize_sec" in payload:
                try:
                    value = float(payload["ads_fovsize_sec"])
                except Exception:
                    return False, "ads_fovsize_sec must be a number"
                if value < 1 or value > 1000:
                    return False, "ads_fovsize_sec must be between 1 and 1000"
                self.config.ads_fovsize_sec = value
                if hasattr(self.tracker, "ads_fovsize_sec"):
                    self.tracker.ads_fovsize_sec = value
        return True, None

    def _patch_trigger(self, payload):
        if not isinstance(payload, dict):
            return False, "payload must be an object"
        with self._lock:
            if "enabletb" in payload:
                self.config.enabletb = bool(payload["enabletb"])
                if hasattr(self.tracker, "enabletb"):
                    self.tracker.enabletb = self.config.enabletb

            if "trigger_type" in payload:
                trigger_type = str(payload["trigger_type"]).lower()
                if trigger_type not in ALLOWED_TRIGGER_TYPES:
                    return False, f"trigger_type must be one of {sorted(ALLOWED_TRIGGER_TYPES)}"
                self.config.trigger_type = trigger_type
                if hasattr(self.tracker, "trigger_type"):
                    self.tracker.trigger_type = trigger_type

            if "tbfovsize" in payload:
                try:
                    value = float(payload["tbfovsize"])
                except Exception:
                    return False, "tbfovsize must be a number"
                if value < 1 or value > 300:
                    return False, "tbfovsize must be between 1 and 300"
                self.config.tbfovsize = value
                if hasattr(self.tracker, "tbfovsize"):
                    self.tracker.tbfovsize = value

            if "tbdelay_min" in payload:
                try:
                    value = float(payload["tbdelay_min"])
                except Exception:
                    return False, "tbdelay_min must be a number"
                if value < 0.0 or value > 1.0:
                    return False, "tbdelay_min must be between 0 and 1.0"
                self.config.tbdelay_min = value
                if hasattr(self.tracker, "tbdelay_min"):
                    self.tracker.tbdelay_min = value

            if "tbdelay_max" in payload:
                try:
                    value = float(payload["tbdelay_max"])
                except Exception:
                    return False, "tbdelay_max must be a number"
                if value < 0.0 or value > 1.0:
                    return False, "tbdelay_max must be between 0 and 1.0"
                self.config.tbdelay_max = value
                if hasattr(self.tracker, "tbdelay_max"):
                    self.tracker.tbdelay_max = value

            if float(getattr(self.config, "tbdelay_min", 0.0)) > float(getattr(self.config, "tbdelay_max", 0.0)):
                return False, "tbdelay_min must be <= tbdelay_max"

            if "trigger_roi_size" in payload:
                try:
                    value = int(payload["trigger_roi_size"])
                except Exception:
                    return False, "trigger_roi_size must be an integer"
                if value < 4 or value > 128:
                    return False, "trigger_roi_size must be between 4 and 128"
                self.config.trigger_roi_size = value
                if hasattr(self.tracker, "trigger_roi_size"):
                    self.tracker.trigger_roi_size = value

            if "trigger_min_pixels" in payload:
                try:
                    value = int(payload["trigger_min_pixels"])
                except Exception:
                    return False, "trigger_min_pixels must be an integer"
                if value < 1 or value > 200:
                    return False, "trigger_min_pixels must be between 1 and 200"
                self.config.trigger_min_pixels = value
                if hasattr(self.tracker, "trigger_min_pixels"):
                    self.tracker.trigger_min_pixels = value

            if "trigger_min_ratio" in payload:
                try:
                    value = float(payload["trigger_min_ratio"])
                except Exception:
                    return False, "trigger_min_ratio must be a number"
                if value < 0.0 or value > 1.0:
                    return False, "trigger_min_ratio must be between 0 and 1"
                self.config.trigger_min_ratio = value
                if hasattr(self.tracker, "trigger_min_ratio"):
                    self.tracker.trigger_min_ratio = value

            if "trigger_ads_fov_enabled" in payload:
                self.config.trigger_ads_fov_enabled = bool(payload["trigger_ads_fov_enabled"])
                if hasattr(self.tracker, "trigger_ads_fov_enabled"):
                    self.tracker.trigger_ads_fov_enabled = self.config.trigger_ads_fov_enabled

            if "trigger_ads_fovsize" in payload:
                try:
                    value = float(payload["trigger_ads_fovsize"])
                except Exception:
                    return False, "trigger_ads_fovsize must be a number"
                if value < 1 or value > 300:
                    return False, "trigger_ads_fovsize must be between 1 and 300"
                self.config.trigger_ads_fovsize = value
                if hasattr(self.tracker, "trigger_ads_fovsize"):
                    self.tracker.trigger_ads_fovsize = value
        return True, None

    def _patch_rcs(self, payload):
        if not isinstance(payload, dict):
            return False, "payload must be an object"
        with self._lock:
            if "enablercs" in payload:
                self.config.enablercs = bool(payload["enablercs"])
                if hasattr(self.tracker, "enablercs"):
                    self.tracker.enablercs = self.config.enablercs

            if "rcs_pull_speed" in payload:
                try:
                    value = int(payload["rcs_pull_speed"])
                except Exception:
                    return False, "rcs_pull_speed must be an integer"
                if value < 1 or value > 20:
                    return False, "rcs_pull_speed must be between 1 and 20"
                self.config.rcs_pull_speed = value
                if hasattr(self.tracker, "rcs_pull_speed"):
                    self.tracker.rcs_pull_speed = value

            if "rcs_activation_delay" in payload:
                try:
                    value = int(payload["rcs_activation_delay"])
                except Exception:
                    return False, "rcs_activation_delay must be an integer"
                if value < 50 or value > 500:
                    return False, "rcs_activation_delay must be between 50 and 500"
                self.config.rcs_activation_delay = value
                if hasattr(self.tracker, "rcs_activation_delay"):
                    self.tracker.rcs_activation_delay = value

            if "rcs_rapid_click_threshold" in payload:
                try:
                    value = int(payload["rcs_rapid_click_threshold"])
                except Exception:
                    return False, "rcs_rapid_click_threshold must be an integer"
                if value < 100 or value > 1000:
                    return False, "rcs_rapid_click_threshold must be between 100 and 1000"
                self.config.rcs_rapid_click_threshold = value
                if hasattr(self.tracker, "rcs_rapid_click_threshold"):
                    self.tracker.rcs_rapid_click_threshold = value

            if "rcs_release_y_enabled" in payload:
                self.config.rcs_release_y_enabled = bool(payload["rcs_release_y_enabled"])
                if hasattr(self.tracker, "rcs_release_y_enabled"):
                    self.tracker.rcs_release_y_enabled = self.config.rcs_release_y_enabled

            if "rcs_release_y_duration" in payload:
                try:
                    value = float(payload["rcs_release_y_duration"])
                except Exception:
                    return False, "rcs_release_y_duration must be a number"
                if value < 0.1 or value > 5.0:
                    return False, "rcs_release_y_duration must be between 0.1 and 5.0"
                self.config.rcs_release_y_duration = value
                if hasattr(self.tracker, "rcs_release_y_duration"):
                    self.tracker.rcs_release_y_duration = value
        return True, None

    def _patch_general(self, payload):
        if not isinstance(payload, dict):
            return False, "payload must be an object"
        with self._lock:
            if "color" in payload:
                color = str(payload["color"]).lower()
                if color not in ALLOWED_COLORS:
                    return False, f"color must be one of {sorted(ALLOWED_COLORS)}"
                self.config.color = color
                if hasattr(self.tracker, "color"):
                    self.tracker.color = color

            if "capture_mode" in payload:
                mode = str(payload["capture_mode"])
                if mode not in ALLOWED_CAPTURE_MODES:
                    return False, f"capture_mode must be one of {sorted(ALLOWED_CAPTURE_MODES)}"
                self.config.capture_mode = mode
                if self.capture_service is not None and hasattr(self.capture_service, "set_mode"):
                    try:
                        self.capture_service.set_mode(mode)
                    except Exception:
                        pass

            if "target_fps" in payload:
                try:
                    value = int(payload["target_fps"])
                except Exception:
                    return False, "target_fps must be an integer"
                if value < 1 or value > 360:
                    return False, "target_fps must be between 1 and 360"
                self.config.target_fps = value
                if hasattr(self.tracker, "set_target_fps"):
                    try:
                        self.tracker.set_target_fps(value)
                    except Exception:
                        pass
                elif hasattr(self.tracker, "_target_fps"):
                    self.tracker._target_fps = float(value)
        return True, None

    def _configs_dir(self):
        return self._base_dir / "configs"

    def _sanitize_config_name(self, name: str):
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(name).strip())
        cleaned = cleaned.strip("._-")
        if not cleaned:
            return ""
        return cleaned

    def _list_configs(self):
        cfg_dir = self._configs_dir()
        cfg_dir.mkdir(parents=True, exist_ok=True)
        names = []
        for p in cfg_dir.glob("*.json"):
            names.append(p.stem)
        names.sort()
        return names

    def _sync_runtime_from_config(self):
        try:
            data = self.config.to_dict()
        except Exception:
            data = {}
        for key, value in data.items():
            if hasattr(self.tracker, key):
                try:
                    setattr(self.tracker, key, value)
                except Exception:
                    pass
        try:
            if hasattr(self.tracker, "set_target_fps"):
                self.tracker.set_target_fps(int(getattr(self.config, "target_fps", 80)))
            elif hasattr(self.tracker, "_target_fps"):
                self.tracker._target_fps = float(getattr(self.config, "target_fps", 80))
        except Exception:
            pass
        try:
            if self.capture_service is not None and hasattr(self.capture_service, "set_mode"):
                self.capture_service.set_mode(str(getattr(self.config, "capture_mode", "NDI")))
        except Exception:
            pass

    def _load_named_config(self, name: str):
        safe = self._sanitize_config_name(name)
        if not safe:
            return False, "invalid config name"
        path = self._configs_dir() / f"{safe}.json"
        if not path.exists():
            return False, f"config not found: {safe}"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return False, f"invalid config file: {exc}"

        with self._lock:
            try:
                self.config.from_dict(payload)
                self._sync_runtime_from_config()
            except Exception as exc:
                return False, f"failed to apply config: {exc}"
        return True, None

    def _save_new_named_config(self, name: str):
        safe = self._sanitize_config_name(name)
        if not safe:
            return False, "invalid config name", None
        path = self._configs_dir() / f"{safe}.json"
        if path.exists():
            return False, f"config already exists: {safe}", None
        try:
            self._configs_dir().mkdir(parents=True, exist_ok=True)
            with self._lock:
                data = self.config.to_dict()
            path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
            return True, None, safe
        except Exception as exc:
            return False, f"failed to save config: {exc}", None
