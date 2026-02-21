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
ALLOWED_KEY_TYPES = {"hold", "toggle"}
ALLOWED_AIMBOT_ACTIVATION_TYPES = {"hold_enable", "hold_disable", "toggle", "use_enable"}
ALLOWED_TRIGGER_ACTIVATION_TYPES = {"hold_enable", "hold_disable", "toggle"}
ALLOWED_TRIGGER_STRAFE_MODES = {"off", "auto", "manual_wait"}
ALLOWED_RGB_COLOR_PROFILES = {"red", "yellow", "purple", "custom"}
ALLOWED_MOUSE_APIS = {"Serial", "Arduino", "SendInput", "Net", "KmboxA", "MakV2", "MakV2Binary", "DHZ", "Ferrum"}
ALLOWED_SERIAL_PORT_MODES = {"Auto", "Manual"}


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
                if path == "/api/v1/state/full":
                    self._json(HTTPStatus.OK, outer._build_full_state())
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
                if parsed.path == "/api/v1/state/full":
                    payload = self._read_json()
                    if payload is None:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
                        return
                    ok, err = outer._patch_full(payload)
                    if not ok:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "validation_error", "message": err})
                        return
                    self._json(HTTPStatus.OK, outer._build_full_state())
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
                "anti_smoke_enabled": bool(getattr(self.config, "anti_smoke_enabled", False)),
                "humanized_aim_enabled": bool(getattr(self.config, "humanized_aim_enabled", False)),
                "mode": str(getattr(self.config, "mode", "Normal")),
                "fovsize": float(getattr(self.config, "fovsize", 100)),
                "normal_x_speed": float(getattr(self.config, "normal_x_speed", 3)),
                "normal_y_speed": float(getattr(self.config, "normal_y_speed", 3)),
                "normalsmooth": float(getattr(self.config, "normalsmooth", 30)),
                "normalsmoothfov": float(getattr(self.config, "normalsmoothfov", 30)),
                "aim_offsetX": float(getattr(self.config, "aim_offsetX", 0)),
                "aim_offsetY": float(getattr(self.config, "aim_offsetY", 0)),
                "aim_type": str(getattr(self.config, "aim_type", "head")),
                "ads_fov_enabled": bool(getattr(self.config, "ads_fov_enabled", False)),
                "ads_fovsize": float(getattr(self.config, "ads_fovsize", getattr(self.config, "fovsize", 100))),
                "selected_mouse_button": int(getattr(self.config, "selected_mouse_button", 1)),
                "aimbot_activation_type": str(getattr(self.config, "aimbot_activation_type", "hold_enable")),
                "ads_key": str(getattr(self.config, "ads_key", "Right Mouse Button")),
                "ads_key_type": str(getattr(self.config, "ads_key_type", "hold")),
                "silent_distance": float(getattr(self.config, "silent_distance", 1.0)),
                "silent_delay": float(getattr(self.config, "silent_delay", 100.0)),
                "silent_move_delay": float(getattr(self.config, "silent_move_delay", 500.0)),
                "silent_return_delay": float(getattr(self.config, "silent_return_delay", 500.0)),
                "ncaf_alpha": float(getattr(self.config, "ncaf_alpha", 1.5)),
                "ncaf_snap_boost": float(getattr(self.config, "ncaf_snap_boost", 0.3)),
                "ncaf_max_step": float(getattr(self.config, "ncaf_max_step", 50.0)),
                "ncaf_min_speed_multiplier": float(getattr(self.config, "ncaf_min_speed_multiplier", 0.01)),
                "ncaf_max_speed_multiplier": float(getattr(self.config, "ncaf_max_speed_multiplier", 10.0)),
                "ncaf_prediction_interval": float(getattr(self.config, "ncaf_prediction_interval", 0.016)),
                "ncaf_snap_radius": float(getattr(self.config, "ncaf_snap_radius", 150.0)),
                "ncaf_near_radius": float(getattr(self.config, "ncaf_near_radius", 50.0)),
                "wm_gravity": float(getattr(self.config, "wm_gravity", 9.0)),
                "wm_wind": float(getattr(self.config, "wm_wind", 3.0)),
                "wm_max_step": float(getattr(self.config, "wm_max_step", 15.0)),
                "wm_min_step": float(getattr(self.config, "wm_min_step", 2.0)),
                "wm_min_delay": float(getattr(self.config, "wm_min_delay", 0.001)),
                "wm_max_delay": float(getattr(self.config, "wm_max_delay", 0.003)),
                "wm_distance_threshold": float(getattr(self.config, "wm_distance_threshold", 50.0)),
                "bezier_segments": int(getattr(self.config, "bezier_segments", 8)),
                "bezier_ctrl_x": float(getattr(self.config, "bezier_ctrl_x", 16.0)),
                "bezier_ctrl_y": float(getattr(self.config, "bezier_ctrl_y", 16.0)),
                "bezier_speed": float(getattr(self.config, "bezier_speed", 1.0)),
                "bezier_delay": float(getattr(self.config, "bezier_delay", 0.002)),
                "connected": self._build_connected_summary(),
                "version": self._get_version(),
            }

    def _build_sec_aimbot_state(self):
        with self._lock:
            return {
                "enableaim_sec": bool(getattr(self.config, "enableaim_sec", False)),
                "anti_smoke_enabled_sec": bool(getattr(self.config, "anti_smoke_enabled_sec", False)),
                "humanized_aim_enabled_sec": bool(getattr(self.config, "humanized_aim_enabled_sec", False)),
                "mode_sec": str(getattr(self.config, "mode_sec", "Normal")),
                "fovsize_sec": float(getattr(self.config, "fovsize_sec", 150)),
                "normal_x_speed_sec": float(getattr(self.config, "normal_x_speed_sec", 2)),
                "normal_y_speed_sec": float(getattr(self.config, "normal_y_speed_sec", 2)),
                "normalsmooth_sec": float(getattr(self.config, "normalsmooth_sec", 20)),
                "normalsmoothfov_sec": float(getattr(self.config, "normalsmoothfov_sec", 20)),
                "aim_offsetX_sec": float(getattr(self.config, "aim_offsetX_sec", 0)),
                "aim_offsetY_sec": float(getattr(self.config, "aim_offsetY_sec", 0)),
                "aim_type_sec": str(getattr(self.config, "aim_type_sec", "head")),
                "ads_fov_enabled_sec": bool(getattr(self.config, "ads_fov_enabled_sec", False)),
                "ads_fovsize_sec": float(getattr(self.config, "ads_fovsize_sec", getattr(self.config, "fovsize_sec", 150))),
                "selected_mouse_button_sec": int(getattr(self.config, "selected_mouse_button_sec", 2)),
                "aimbot_activation_type_sec": str(getattr(self.config, "aimbot_activation_type_sec", "hold_enable")),
                "ads_key_sec": str(getattr(self.config, "ads_key_sec", "Right Mouse Button")),
                "ads_key_type_sec": str(getattr(self.config, "ads_key_type_sec", "hold")),
                "ncaf_alpha_sec": float(getattr(self.config, "ncaf_alpha_sec", 1.5)),
                "ncaf_snap_boost_sec": float(getattr(self.config, "ncaf_snap_boost_sec", 0.3)),
                "ncaf_max_step_sec": float(getattr(self.config, "ncaf_max_step_sec", 50.0)),
                "ncaf_min_speed_multiplier_sec": float(getattr(self.config, "ncaf_min_speed_multiplier_sec", 0.01)),
                "ncaf_max_speed_multiplier_sec": float(getattr(self.config, "ncaf_max_speed_multiplier_sec", 10.0)),
                "ncaf_prediction_interval_sec": float(getattr(self.config, "ncaf_prediction_interval_sec", 0.016)),
                "ncaf_snap_radius_sec": float(getattr(self.config, "ncaf_snap_radius_sec", 150.0)),
                "ncaf_near_radius_sec": float(getattr(self.config, "ncaf_near_radius_sec", 50.0)),
                "wm_gravity_sec": float(getattr(self.config, "wm_gravity_sec", 9.0)),
                "wm_wind_sec": float(getattr(self.config, "wm_wind_sec", 3.0)),
                "wm_max_step_sec": float(getattr(self.config, "wm_max_step_sec", 15.0)),
                "wm_min_step_sec": float(getattr(self.config, "wm_min_step_sec", 2.0)),
                "wm_min_delay_sec": float(getattr(self.config, "wm_min_delay_sec", 0.001)),
                "wm_max_delay_sec": float(getattr(self.config, "wm_max_delay_sec", 0.003)),
                "wm_distance_threshold_sec": float(getattr(self.config, "wm_distance_threshold_sec", 50.0)),
                "bezier_segments_sec": int(getattr(self.config, "bezier_segments_sec", 8)),
                "bezier_ctrl_x_sec": float(getattr(self.config, "bezier_ctrl_x_sec", 16.0)),
                "bezier_ctrl_y_sec": float(getattr(self.config, "bezier_ctrl_y_sec", 16.0)),
                "bezier_speed_sec": float(getattr(self.config, "bezier_speed_sec", 1.0)),
                "bezier_delay_sec": float(getattr(self.config, "bezier_delay_sec", 0.002)),
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
                "tbhold_min": float(getattr(self.config, "tbhold_min", 40)),
                "tbhold_max": float(getattr(self.config, "tbhold_max", 60)),
                "tbcooldown_min": float(getattr(self.config, "tbcooldown_min", 0.0)),
                "tbcooldown_max": float(getattr(self.config, "tbcooldown_max", 0.0)),
                "trigger_confirm_frames": int(getattr(self.config, "trigger_confirm_frames", 2)),
                "tbburst_count_min": int(getattr(self.config, "tbburst_count_min", 1)),
                "tbburst_count_max": int(getattr(self.config, "tbburst_count_max", 1)),
                "tbburst_interval_min": float(getattr(self.config, "tbburst_interval_min", 0.0)),
                "tbburst_interval_max": float(getattr(self.config, "tbburst_interval_max", 0.0)),
                "trigger_roi_size": int(getattr(self.config, "trigger_roi_size", 8)),
                "trigger_min_pixels": int(getattr(self.config, "trigger_min_pixels", 4)),
                "trigger_min_ratio": float(getattr(self.config, "trigger_min_ratio", 0.03)),
                "trigger_ads_fov_enabled": bool(getattr(self.config, "trigger_ads_fov_enabled", False)),
                "trigger_ads_fovsize": float(getattr(self.config, "trigger_ads_fovsize", 5)),
                "selected_tb_btn": int(getattr(self.config, "selected_tb_btn", 1)),
                "trigger_activation_type": str(getattr(self.config, "trigger_activation_type", "hold_enable")),
                "trigger_ads_key": str(getattr(self.config, "trigger_ads_key", "Right Mouse Button")),
                "trigger_ads_key_type": str(getattr(self.config, "trigger_ads_key_type", "hold")),
                "trigger_strafe_mode": str(getattr(self.config, "trigger_strafe_mode", "off")),
                "trigger_strafe_auto_lead_ms": int(getattr(self.config, "trigger_strafe_auto_lead_ms", 8)),
                "trigger_strafe_manual_neutral_ms": int(getattr(self.config, "trigger_strafe_manual_neutral_ms", 0)),
                "rgb_color_profile": str(getattr(self.config, "rgb_color_profile", "purple")),
                "rgb_custom_r": int(getattr(self.config, "rgb_custom_r", 161)),
                "rgb_custom_g": int(getattr(self.config, "rgb_custom_g", 69)),
                "rgb_custom_b": int(getattr(self.config, "rgb_custom_b", 163)),
                "rgb_tbdelay_min": float(getattr(self.config, "rgb_tbdelay_min", 0.08)),
                "rgb_tbdelay_max": float(getattr(self.config, "rgb_tbdelay_max", 0.15)),
                "rgb_tbhold_min": float(getattr(self.config, "rgb_tbhold_min", 40)),
                "rgb_tbhold_max": float(getattr(self.config, "rgb_tbhold_max", 60)),
                "rgb_tbcooldown_min": float(getattr(self.config, "rgb_tbcooldown_min", 0.0)),
                "rgb_tbcooldown_max": float(getattr(self.config, "rgb_tbcooldown_max", 0.0)),
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
                "in_game_sens": float(getattr(self.config, "in_game_sens", 0.235)),
                "mouse_api": str(getattr(self.config, "mouse_api", "Serial")),
                "auto_connect_mouse_api": bool(getattr(self.config, "auto_connect_mouse_api", False)),
                "serial_port_mode": str(getattr(self.config, "serial_port_mode", "Auto")),
                "serial_port": str(getattr(self.config, "serial_port", "")),
                "serial_auto_switch_4m": bool(getattr(self.config, "serial_auto_switch_4m", False)),
                "arduino_port": str(getattr(self.config, "arduino_port", "")),
                "arduino_baud": int(getattr(self.config, "arduino_baud", 115200)),
                "net_ip": str(getattr(self.config, "net_ip", "192.168.2.188")),
                "net_port": str(getattr(self.config, "net_port", "6234")),
                "net_uuid": str(getattr(self.config, "net_uuid", "")),
                "kmboxa_vid_pid": str(getattr(self.config, "kmboxa_vid_pid", "0/0")),
                "makv2_port": str(getattr(self.config, "makv2_port", "")),
                "makv2_baud": int(getattr(self.config, "makv2_baud", 4000000)),
                "dhz_ip": str(getattr(self.config, "dhz_ip", "192.168.2.188")),
                "dhz_port": str(getattr(self.config, "dhz_port", "5000")),
                "dhz_random": int(getattr(self.config, "dhz_random", 0)),
                "custom_hsv_min_h": int(getattr(self.config, "custom_hsv_min_h", 0)),
                "custom_hsv_min_s": int(getattr(self.config, "custom_hsv_min_s", 0)),
                "custom_hsv_min_v": int(getattr(self.config, "custom_hsv_min_v", 0)),
                "custom_hsv_max_h": int(getattr(self.config, "custom_hsv_max_h", 179)),
                "custom_hsv_max_s": int(getattr(self.config, "custom_hsv_max_s", 255)),
                "custom_hsv_max_v": int(getattr(self.config, "custom_hsv_max_v", 255)),
                "detection_merge_distance": int(getattr(self.config, "detection_merge_distance", 12)),
                "detection_min_contour_points": int(getattr(self.config, "detection_min_contour_points", 5)),
                "button_mask_enabled": bool(getattr(self.config, "button_mask_enabled", False)),
                "mask_left_button": bool(getattr(self.config, "mask_left_button", False)),
                "mask_right_button": bool(getattr(self.config, "mask_right_button", False)),
                "mask_middle_button": bool(getattr(self.config, "mask_middle_button", False)),
                "mask_side4_button": bool(getattr(self.config, "mask_side4_button", False)),
                "mask_side5_button": bool(getattr(self.config, "mask_side5_button", False)),
                "mouse_lock_main_x": bool(getattr(self.config, "mouse_lock_main_x", False)),
                "mouse_lock_main_y": bool(getattr(self.config, "mouse_lock_main_y", False)),
                "mouse_lock_sec_x": bool(getattr(self.config, "mouse_lock_sec_x", False)),
                "mouse_lock_sec_y": bool(getattr(self.config, "mouse_lock_sec_y", False)),
                "udp_ip": str(getattr(self.config, "udp_ip", "127.0.0.1")),
                "udp_port": str(getattr(self.config, "udp_port", "1234")),
                "last_ndi_source": str(getattr(self.config, "last_ndi_source", "") or ""),
                "ndi_fov_enabled": bool(getattr(self.config, "ndi_fov_enabled", False)),
                "ndi_fov": int(getattr(self.config, "ndi_fov", 320)),
                "udp_fov_enabled": bool(getattr(self.config, "udp_fov_enabled", False)),
                "udp_fov": int(getattr(self.config, "udp_fov", 320)),
                "mss_monitor_index": int(getattr(self.config, "mss_monitor_index", 1)),
                "mss_fov_x": int(getattr(self.config, "mss_fov_x", 320)),
                "mss_fov_y": int(getattr(self.config, "mss_fov_y", 320)),
                "capture_device_index": int(getattr(self.config, "capture_device_index", 0)),
                "capture_width": int(getattr(self.config, "capture_width", 1920)),
                "capture_height": int(getattr(self.config, "capture_height", 1080)),
                "capture_fps": int(getattr(self.config, "capture_fps", 240)),
                "capture_range_x": int(getattr(self.config, "capture_range_x", 128)),
                "capture_range_y": int(getattr(self.config, "capture_range_y", 128)),
                "capture_offset_x": int(getattr(self.config, "capture_offset_x", 0)),
                "capture_offset_y": int(getattr(self.config, "capture_offset_y", 0)),
                "connected": self._build_connected_summary(),
                "version": self._get_version(),
            }

    def _build_full_state(self):
        with self._lock:
            try:
                data = self.config.to_dict()
            except Exception:
                data = {}
            if not isinstance(data, dict):
                data = {}
            out = dict(data)
            out["connected"] = self._build_connected_summary()
            out["version"] = self._get_version()
            return out

    def _set_tracker_value(self, key, value, tracker_key=None):
        t_key = tracker_key or key
        if hasattr(self.tracker, t_key):
            try:
                setattr(self.tracker, t_key, value)
            except Exception:
                pass

    def _set_bool_field(self, payload, key, tracker_key=None):
        if key not in payload:
            return True, None
        value = bool(payload[key])
        setattr(self.config, key, value)
        self._set_tracker_value(key, value, tracker_key=tracker_key)
        return True, None

    def _set_choice_field(self, payload, key, allowed, tracker_key=None, lower=False):
        if key not in payload:
            return True, None
        value = str(payload[key]).strip()
        if lower:
            value = value.lower()
        if value not in allowed:
            return False, f"{key} must be one of {sorted(allowed)}"
        setattr(self.config, key, value)
        self._set_tracker_value(key, value, tracker_key=tracker_key)
        return True, None

    def _set_float_field(self, payload, key, min_value, max_value, tracker_key=None):
        if key not in payload:
            return True, None
        try:
            value = float(payload[key])
        except Exception:
            return False, f"{key} must be a number"
        if value < float(min_value) or value > float(max_value):
            return False, f"{key} must be between {min_value} and {max_value}"
        setattr(self.config, key, value)
        self._set_tracker_value(key, value, tracker_key=tracker_key)
        return True, None

    def _set_int_field(self, payload, key, min_value, max_value, tracker_key=None):
        if key not in payload:
            return True, None
        try:
            value = int(payload[key])
        except Exception:
            return False, f"{key} must be an integer"
        if value < int(min_value) or value > int(max_value):
            return False, f"{key} must be between {min_value} and {max_value}"
        setattr(self.config, key, value)
        self._set_tracker_value(key, value, tracker_key=tracker_key)
        return True, None

    def _set_string_field(self, payload, key, tracker_key=None, allow_empty=False):
        if key not in payload:
            return True, None
        value = str(payload[key]).strip()
        if not allow_empty and not value:
            return False, f"{key} must not be empty"
        setattr(self.config, key, value)
        self._set_tracker_value(key, value, tracker_key=tracker_key)
        return True, None

    def _patch_main_aimbot(self, payload):
        if not isinstance(payload, dict):
            return False, "payload must be an object"

        with self._lock:
            for setter, key, args in (
                (self._set_bool_field, "enableaim", {}),
                (self._set_bool_field, "anti_smoke_enabled", {}),
                (self._set_bool_field, "humanized_aim_enabled", {}),
                (self._set_choice_field, "mode", {"allowed": ALLOWED_MODES}),
                (self._set_float_field, "fovsize", {"min_value": 1, "max_value": 1000}),
                (self._set_float_field, "normal_x_speed", {"min_value": 0.1, "max_value": 2000}),
                (self._set_float_field, "normal_y_speed", {"min_value": 0.1, "max_value": 2000}),
                (self._set_float_field, "normalsmooth", {"min_value": 1, "max_value": 30}),
                (self._set_float_field, "normalsmoothfov", {"min_value": 1, "max_value": 30}),
                (self._set_float_field, "aim_offsetX", {"min_value": -100, "max_value": 100}),
                (self._set_float_field, "aim_offsetY", {"min_value": -100, "max_value": 100}),
                (self._set_choice_field, "aim_type", {"allowed": ALLOWED_AIM_TYPES, "lower": True}),
                (self._set_bool_field, "ads_fov_enabled", {}),
                (self._set_float_field, "ads_fovsize", {"min_value": 1, "max_value": 1000}),
                (self._set_int_field, "selected_mouse_button", {"min_value": 0, "max_value": 4}),
                (
                    self._set_choice_field,
                    "aimbot_activation_type",
                    {"allowed": ALLOWED_AIMBOT_ACTIVATION_TYPES, "lower": True},
                ),
                (self._set_string_field, "ads_key", {"allow_empty": False}),
                (self._set_choice_field, "ads_key_type", {"allowed": ALLOWED_KEY_TYPES, "lower": True}),
                (self._set_float_field, "silent_distance", {"min_value": 0.1, "max_value": 10.0}),
                (self._set_float_field, "silent_delay", {"min_value": 0.001, "max_value": 300.0}),
                (self._set_float_field, "silent_move_delay", {"min_value": 0.001, "max_value": 300.0}),
                (self._set_float_field, "silent_return_delay", {"min_value": 0.001, "max_value": 300.0}),
                (self._set_float_field, "ncaf_alpha", {"min_value": 0.1, "max_value": 5.0}),
                (self._set_float_field, "ncaf_snap_boost", {"min_value": 0.01, "max_value": 2.0}),
                (self._set_float_field, "ncaf_max_step", {"min_value": 1, "max_value": 200}),
                (self._set_float_field, "ncaf_min_speed_multiplier", {"min_value": 0.01, "max_value": 1.0}),
                (self._set_float_field, "ncaf_max_speed_multiplier", {"min_value": 1.0, "max_value": 20.0}),
                (self._set_float_field, "ncaf_prediction_interval", {"min_value": 0.001, "max_value": 0.1}),
                (self._set_float_field, "ncaf_snap_radius", {"min_value": 10, "max_value": 500}),
                (self._set_float_field, "ncaf_near_radius", {"min_value": 5, "max_value": 400}),
                (self._set_float_field, "wm_gravity", {"min_value": 0.1, "max_value": 30.0}),
                (self._set_float_field, "wm_wind", {"min_value": 0.1, "max_value": 20.0}),
                (self._set_float_field, "wm_max_step", {"min_value": 1, "max_value": 100}),
                (self._set_float_field, "wm_min_step", {"min_value": 0.1, "max_value": 20.0}),
                (self._set_float_field, "wm_min_delay", {"min_value": 0.0001, "max_value": 0.05}),
                (self._set_float_field, "wm_max_delay", {"min_value": 0.0001, "max_value": 0.05}),
                (self._set_float_field, "wm_distance_threshold", {"min_value": 10, "max_value": 200}),
                (self._set_int_field, "bezier_segments", {"min_value": 1, "max_value": 30}),
                (self._set_float_field, "bezier_ctrl_x", {"min_value": 0.0, "max_value": 100.0}),
                (self._set_float_field, "bezier_ctrl_y", {"min_value": 0.0, "max_value": 100.0}),
                (self._set_float_field, "bezier_speed", {"min_value": 0.1, "max_value": 20.0}),
                (self._set_float_field, "bezier_delay", {"min_value": 0.0001, "max_value": 0.05}),
            ):
                ok, err = setter(payload, key, **args)
                if not ok:
                    return False, err

        return True, None

    def _patch_sec_aimbot(self, payload):
        if not isinstance(payload, dict):
            return False, "payload must be an object"
        with self._lock:
            for setter, key, args in (
                (self._set_bool_field, "enableaim_sec", {}),
                (self._set_bool_field, "anti_smoke_enabled_sec", {}),
                (self._set_bool_field, "humanized_aim_enabled_sec", {}),
                (self._set_choice_field, "mode_sec", {"allowed": ALLOWED_MODES}),
                (self._set_float_field, "fovsize_sec", {"min_value": 1, "max_value": 1000}),
                (self._set_float_field, "normal_x_speed_sec", {"min_value": 0.1, "max_value": 2000}),
                (self._set_float_field, "normal_y_speed_sec", {"min_value": 0.1, "max_value": 2000}),
                (self._set_float_field, "normalsmooth_sec", {"min_value": 1, "max_value": 30}),
                (self._set_float_field, "normalsmoothfov_sec", {"min_value": 1, "max_value": 30}),
                (self._set_float_field, "aim_offsetX_sec", {"min_value": -100, "max_value": 100}),
                (self._set_float_field, "aim_offsetY_sec", {"min_value": -100, "max_value": 100}),
                (self._set_choice_field, "aim_type_sec", {"allowed": ALLOWED_AIM_TYPES, "lower": True}),
                (self._set_bool_field, "ads_fov_enabled_sec", {}),
                (self._set_float_field, "ads_fovsize_sec", {"min_value": 1, "max_value": 1000}),
                (self._set_int_field, "selected_mouse_button_sec", {"min_value": 0, "max_value": 4}),
                (
                    self._set_choice_field,
                    "aimbot_activation_type_sec",
                    {"allowed": ALLOWED_AIMBOT_ACTIVATION_TYPES, "lower": True},
                ),
                (self._set_string_field, "ads_key_sec", {"allow_empty": False}),
                (self._set_choice_field, "ads_key_type_sec", {"allowed": ALLOWED_KEY_TYPES, "lower": True}),
                (self._set_float_field, "ncaf_alpha_sec", {"min_value": 0.1, "max_value": 5.0}),
                (self._set_float_field, "ncaf_snap_boost_sec", {"min_value": 0.01, "max_value": 2.0}),
                (self._set_float_field, "ncaf_max_step_sec", {"min_value": 1, "max_value": 200}),
                (
                    self._set_float_field,
                    "ncaf_min_speed_multiplier_sec",
                    {"min_value": 0.01, "max_value": 1.0},
                ),
                (
                    self._set_float_field,
                    "ncaf_max_speed_multiplier_sec",
                    {"min_value": 1.0, "max_value": 20.0},
                ),
                (self._set_float_field, "ncaf_prediction_interval_sec", {"min_value": 0.001, "max_value": 0.1}),
                (self._set_float_field, "ncaf_snap_radius_sec", {"min_value": 10, "max_value": 500}),
                (self._set_float_field, "ncaf_near_radius_sec", {"min_value": 5, "max_value": 400}),
                (self._set_float_field, "wm_gravity_sec", {"min_value": 0.1, "max_value": 30.0}),
                (self._set_float_field, "wm_wind_sec", {"min_value": 0.1, "max_value": 20.0}),
                (self._set_float_field, "wm_max_step_sec", {"min_value": 1, "max_value": 100}),
                (self._set_float_field, "wm_min_step_sec", {"min_value": 0.1, "max_value": 20.0}),
                (self._set_float_field, "wm_min_delay_sec", {"min_value": 0.0001, "max_value": 0.05}),
                (self._set_float_field, "wm_max_delay_sec", {"min_value": 0.0001, "max_value": 0.05}),
                (self._set_float_field, "wm_distance_threshold_sec", {"min_value": 10, "max_value": 200}),
                (self._set_int_field, "bezier_segments_sec", {"min_value": 1, "max_value": 30}),
                (self._set_float_field, "bezier_ctrl_x_sec", {"min_value": 0.0, "max_value": 100.0}),
                (self._set_float_field, "bezier_ctrl_y_sec", {"min_value": 0.0, "max_value": 100.0}),
                (self._set_float_field, "bezier_speed_sec", {"min_value": 0.1, "max_value": 20.0}),
                (self._set_float_field, "bezier_delay_sec", {"min_value": 0.0001, "max_value": 0.05}),
            ):
                ok, err = setter(payload, key, **args)
                if not ok:
                    return False, err
        return True, None

    def _patch_trigger(self, payload):
        if not isinstance(payload, dict):
            return False, "payload must be an object"
        with self._lock:
            for setter, key, args in (
                (self._set_bool_field, "enabletb", {}),
                (self._set_choice_field, "trigger_type", {"allowed": ALLOWED_TRIGGER_TYPES, "lower": True}),
                (self._set_float_field, "tbfovsize", {"min_value": 1, "max_value": 300}),
                (self._set_float_field, "tbdelay_min", {"min_value": 0.0, "max_value": 1.0}),
                (self._set_float_field, "tbdelay_max", {"min_value": 0.0, "max_value": 1.0}),
                (self._set_float_field, "tbhold_min", {"min_value": 5, "max_value": 500}),
                (self._set_float_field, "tbhold_max", {"min_value": 5, "max_value": 500}),
                (self._set_float_field, "tbcooldown_min", {"min_value": 0.0, "max_value": 5.0}),
                (self._set_float_field, "tbcooldown_max", {"min_value": 0.0, "max_value": 5.0}),
                (self._set_int_field, "tbburst_count_min", {"min_value": 1, "max_value": 10}),
                (self._set_int_field, "tbburst_count_max", {"min_value": 1, "max_value": 10}),
                (self._set_float_field, "tbburst_interval_min", {"min_value": 0.0, "max_value": 500.0}),
                (self._set_float_field, "tbburst_interval_max", {"min_value": 0.0, "max_value": 500.0}),
                (self._set_int_field, "trigger_roi_size", {"min_value": 4, "max_value": 128}),
                (self._set_int_field, "trigger_min_pixels", {"min_value": 1, "max_value": 200}),
                (self._set_float_field, "trigger_min_ratio", {"min_value": 0.0, "max_value": 1.0}),
                (self._set_int_field, "trigger_confirm_frames", {"min_value": 1, "max_value": 10}),
                (self._set_bool_field, "trigger_ads_fov_enabled", {}),
                (self._set_float_field, "trigger_ads_fovsize", {"min_value": 1, "max_value": 300}),
                (self._set_int_field, "selected_tb_btn", {"min_value": 0, "max_value": 4}),
                (
                    self._set_choice_field,
                    "trigger_activation_type",
                    {"allowed": ALLOWED_TRIGGER_ACTIVATION_TYPES, "lower": True},
                ),
                (self._set_string_field, "trigger_ads_key", {"allow_empty": False}),
                (
                    self._set_choice_field,
                    "trigger_ads_key_type",
                    {"allowed": ALLOWED_KEY_TYPES, "lower": True},
                ),
                (
                    self._set_choice_field,
                    "trigger_strafe_mode",
                    {"allowed": ALLOWED_TRIGGER_STRAFE_MODES, "lower": True},
                ),
                (self._set_int_field, "trigger_strafe_auto_lead_ms", {"min_value": 0, "max_value": 50}),
                (self._set_int_field, "trigger_strafe_manual_neutral_ms", {"min_value": 0, "max_value": 300}),
                (
                    self._set_choice_field,
                    "rgb_color_profile",
                    {"allowed": ALLOWED_RGB_COLOR_PROFILES, "lower": True},
                ),
                (self._set_int_field, "rgb_custom_r", {"min_value": 0, "max_value": 255}),
                (self._set_int_field, "rgb_custom_g", {"min_value": 0, "max_value": 255}),
                (self._set_int_field, "rgb_custom_b", {"min_value": 0, "max_value": 255}),
                (self._set_float_field, "rgb_tbdelay_min", {"min_value": 0.0, "max_value": 1.0}),
                (self._set_float_field, "rgb_tbdelay_max", {"min_value": 0.0, "max_value": 1.0}),
                (self._set_float_field, "rgb_tbhold_min", {"min_value": 5, "max_value": 500}),
                (self._set_float_field, "rgb_tbhold_max", {"min_value": 5, "max_value": 500}),
                (self._set_float_field, "rgb_tbcooldown_min", {"min_value": 0.0, "max_value": 5.0}),
                (self._set_float_field, "rgb_tbcooldown_max", {"min_value": 0.0, "max_value": 5.0}),
            ):
                ok, err = setter(payload, key, **args)
                if not ok:
                    return False, err

            for min_key, max_key in (
                ("tbdelay_min", "tbdelay_max"),
                ("tbhold_min", "tbhold_max"),
                ("tbcooldown_min", "tbcooldown_max"),
                ("tbburst_count_min", "tbburst_count_max"),
                ("tbburst_interval_min", "tbburst_interval_max"),
                ("rgb_tbdelay_min", "rgb_tbdelay_max"),
                ("rgb_tbhold_min", "rgb_tbhold_max"),
                ("rgb_tbcooldown_min", "rgb_tbcooldown_max"),
            ):
                if float(getattr(self.config, min_key, 0.0)) > float(getattr(self.config, max_key, 0.0)):
                    return False, f"{min_key} must be <= {max_key}"
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
            for setter, key, args in (
                (self._set_choice_field, "color", {"allowed": ALLOWED_COLORS, "lower": True}),
                (self._set_float_field, "in_game_sens", {"min_value": 0.1, "max_value": 20.0}),
                (self._set_choice_field, "mouse_api", {"allowed": ALLOWED_MOUSE_APIS}),
                (self._set_bool_field, "auto_connect_mouse_api", {}),
                (self._set_choice_field, "serial_port_mode", {"allowed": ALLOWED_SERIAL_PORT_MODES}),
                (self._set_string_field, "serial_port", {"allow_empty": True}),
                (self._set_bool_field, "serial_auto_switch_4m", {}),
                (self._set_string_field, "arduino_port", {"allow_empty": True}),
                (self._set_int_field, "arduino_baud", {"min_value": 1200, "max_value": 10000000}),
                (self._set_string_field, "net_ip", {"allow_empty": True}),
                (self._set_string_field, "net_port", {"allow_empty": True}),
                (self._set_string_field, "net_uuid", {"allow_empty": True}),
                (self._set_string_field, "kmboxa_vid_pid", {"allow_empty": True}),
                (self._set_string_field, "makv2_port", {"allow_empty": True}),
                (self._set_int_field, "makv2_baud", {"min_value": 1200, "max_value": 10000000}),
                (self._set_string_field, "dhz_ip", {"allow_empty": True}),
                (self._set_string_field, "dhz_port", {"allow_empty": True}),
                (self._set_int_field, "dhz_random", {"min_value": 0, "max_value": 255}),
                (self._set_int_field, "custom_hsv_min_h", {"min_value": 0, "max_value": 179}),
                (self._set_int_field, "custom_hsv_min_s", {"min_value": 0, "max_value": 255}),
                (self._set_int_field, "custom_hsv_min_v", {"min_value": 0, "max_value": 255}),
                (self._set_int_field, "custom_hsv_max_h", {"min_value": 0, "max_value": 179}),
                (self._set_int_field, "custom_hsv_max_s", {"min_value": 0, "max_value": 255}),
                (self._set_int_field, "custom_hsv_max_v", {"min_value": 0, "max_value": 255}),
                (self._set_int_field, "detection_merge_distance", {"min_value": 1, "max_value": 1000}),
                (self._set_int_field, "detection_min_contour_points", {"min_value": 1, "max_value": 200}),
                (self._set_bool_field, "button_mask_enabled", {}),
                (self._set_bool_field, "mask_left_button", {}),
                (self._set_bool_field, "mask_right_button", {}),
                (self._set_bool_field, "mask_middle_button", {}),
                (self._set_bool_field, "mask_side4_button", {}),
                (self._set_bool_field, "mask_side5_button", {}),
                (self._set_bool_field, "mouse_lock_main_x", {}),
                (self._set_bool_field, "mouse_lock_main_y", {}),
                (self._set_bool_field, "mouse_lock_sec_x", {}),
                (self._set_bool_field, "mouse_lock_sec_y", {}),
                (self._set_string_field, "udp_ip", {"allow_empty": True}),
                (self._set_string_field, "udp_port", {"allow_empty": True}),
                (self._set_string_field, "last_ndi_source", {"allow_empty": True}),
                (self._set_bool_field, "ndi_fov_enabled", {}),
                (self._set_int_field, "ndi_fov", {"min_value": 16, "max_value": 1920}),
                (self._set_bool_field, "udp_fov_enabled", {}),
                (self._set_int_field, "udp_fov", {"min_value": 16, "max_value": 1920}),
                (self._set_int_field, "mss_monitor_index", {"min_value": 1, "max_value": 32}),
                (self._set_int_field, "mss_fov_x", {"min_value": 64, "max_value": 4096}),
                (self._set_int_field, "mss_fov_y", {"min_value": 64, "max_value": 4096}),
                (self._set_int_field, "capture_device_index", {"min_value": 0, "max_value": 32}),
                (self._set_int_field, "capture_width", {"min_value": 64, "max_value": 7680}),
                (self._set_int_field, "capture_height", {"min_value": 64, "max_value": 7680}),
                (self._set_int_field, "capture_fps", {"min_value": 1, "max_value": 1000}),
                (self._set_int_field, "capture_range_x", {"min_value": 128, "max_value": 7680}),
                (self._set_int_field, "capture_range_y", {"min_value": 128, "max_value": 7680}),
                (self._set_int_field, "capture_offset_x", {"min_value": -5000, "max_value": 5000}),
                (self._set_int_field, "capture_offset_y", {"min_value": -5000, "max_value": 5000}),
            ):
                ok, err = setter(payload, key, **args)
                if not ok:
                    return False, err

            if "net_uuid" in payload:
                self.config.net_mac = str(getattr(self.config, "net_uuid", ""))

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

    def _patch_full(self, payload):
        if not isinstance(payload, dict):
            return False, "payload must be an object"

        with self._lock:
            try:
                current = self.config.to_dict()
            except Exception:
                current = {}
            if not isinstance(current, dict):
                return False, "config does not support full state patch"

            blocked = {"connected", "version"}
            unknown = [k for k in payload.keys() if k not in current and k not in blocked]
            if unknown:
                return False, f"unknown fields: {', '.join(sorted(unknown)[:10])}"

            for key, value in payload.items():
                if key in blocked:
                    continue
                current[key] = value

            try:
                self.config.from_dict(current)
                self._sync_runtime_from_config()
            except Exception as exc:
                return False, f"failed to apply full state: {exc}"
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
