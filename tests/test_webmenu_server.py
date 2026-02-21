import json
import unittest
import urllib.request
from types import SimpleNamespace
import tempfile
from pathlib import Path

from src.webmenu.server import WebMenuServer


class _DummyCapture:
    def is_connected(self):
        return False


def _build_dummy():
    cfg = SimpleNamespace(
        webmenu_enabled=True,
        webmenu_host="127.0.0.1",
        webmenu_port=0,
        webmenu_allow_lan_only=True,
        webmenu_poll_ms=750,
        enableaim=True,
        mode="Normal",
        fovsize=100.0,
        normal_x_speed=3.0,
        normal_y_speed=3.0,
        normalsmooth=10.0,
        aim_type="head",
        ads_fov_enabled=False,
        ads_fovsize=100.0,
        capture_mode="NDI",
        color="purple",
        target_fps=80,
        enableaim_sec=False,
        mode_sec="Normal",
        fovsize_sec=150.0,
        normal_x_speed_sec=2.0,
        normal_y_speed_sec=2.0,
        normalsmooth_sec=20.0,
        aim_type_sec="head",
        ads_fov_enabled_sec=False,
        ads_fovsize_sec=150.0,
        enabletb=False,
        trigger_type="current",
        tbfovsize=5.0,
        trigger_roi_size=8,
        trigger_min_pixels=4,
        trigger_min_ratio=0.03,
        enablercs=False,
        rcs_pull_speed=10,
        rcs_activation_delay=100,
        rcs_rapid_click_threshold=200,
        rcs_release_y_enabled=False,
        rcs_release_y_duration=1.0,
    )
    cfg.to_dict = lambda: {
        k: v
        for k, v in cfg.__dict__.items()
        if not callable(v)
    }
    cfg.from_dict = lambda data: [setattr(cfg, k, v) for k, v in data.items()]
    cfg.save_to_file = lambda: None
    tracker = SimpleNamespace(
        enableaim=True,
        mode="Normal",
        fovsize=100.0,
        normal_x_speed=3.0,
        normal_y_speed=3.0,
        normalsmooth=10.0,
        aim_type="head",
        ads_fov_enabled=False,
        ads_fovsize=100.0,
        enableaim_sec=False,
        mode_sec="Normal",
        fovsize_sec=150.0,
        normal_x_speed_sec=2.0,
        normal_y_speed_sec=2.0,
        normalsmooth_sec=20.0,
        aim_type_sec="head",
        ads_fov_enabled_sec=False,
        ads_fovsize_sec=150.0,
        enabletb=False,
        trigger_type="current",
        tbfovsize=5.0,
        trigger_roi_size=8,
        trigger_min_pixels=4,
        trigger_min_ratio=0.03,
        enablercs=False,
        rcs_pull_speed=10,
        rcs_activation_delay=100,
        rcs_rapid_click_threshold=200,
        rcs_release_y_enabled=False,
        rcs_release_y_duration=1.0,
    )
    tracker.set_target_fps = lambda v: setattr(tracker, "_target_fps", float(v))
    return cfg, tracker


class WebMenuServerTests(unittest.TestCase):
    def test_lan_filter(self):
        self.assertTrue(WebMenuServer.is_lan_or_loopback_ip("127.0.0.1"))
        self.assertTrue(WebMenuServer.is_lan_or_loopback_ip("192.168.0.20"))
        self.assertTrue(WebMenuServer.is_lan_or_loopback_ip("10.0.0.8"))
        self.assertFalse(WebMenuServer.is_lan_or_loopback_ip("8.8.8.8"))
        self.assertFalse(WebMenuServer.is_lan_or_loopback_ip("not-an-ip"))

    def test_patch_validation(self):
        cfg, tracker = _build_dummy()
        server = WebMenuServer(cfg, tracker, _DummyCapture(), version_provider=lambda: "1.0.0")

        ok, err = server._patch_main_aimbot({"mode": "NCAF", "fovsize": 80, "aim_type": "body"})
        self.assertTrue(ok, err)
        self.assertEqual(cfg.mode, "NCAF")
        self.assertEqual(tracker.mode, "NCAF")
        self.assertEqual(cfg.aim_type, "body")

        ok, err = server._patch_main_aimbot({"mode": "Invalid"})
        self.assertFalse(ok)
        self.assertIn("mode must be one of", err)

        ok, err = server._patch_main_aimbot({"fovsize": 20000})
        self.assertFalse(ok)
        self.assertIn("between 1 and 1000", err)

    def test_integration_health_and_patch(self):
        cfg, tracker = _build_dummy()
        server = WebMenuServer(cfg, tracker, _DummyCapture(), version_provider=lambda: "1.0.0")
        server.start()
        try:
            port = server._server.server_address[1]
            base = f"http://127.0.0.1:{port}"

            with urllib.request.urlopen(f"{base}/api/v1/health", timeout=2) as resp:
                health = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(health.get("ok"))

            req = urllib.request.Request(
                f"{base}/api/v1/state/main-aimbot",
                data=json.dumps({"normal_x_speed": 10.5}).encode("utf-8"),
                method="PATCH",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(float(payload["normal_x_speed"]), 10.5)
                self.assertEqual(float(cfg.normal_x_speed), 10.5)
        finally:
            server.stop()

    def test_patch_other_sections(self):
        cfg, tracker = _build_dummy()
        server = WebMenuServer(cfg, tracker, _DummyCapture(), version_provider=lambda: "1.0.0")

        ok, err = server._patch_general({"capture_mode": "UDP", "color": "yellow", "target_fps": 120})
        self.assertTrue(ok, err)
        self.assertEqual(cfg.capture_mode, "UDP")
        self.assertEqual(cfg.color, "yellow")
        self.assertEqual(cfg.target_fps, 120)

        ok, err = server._patch_sec_aimbot({"enableaim_sec": True, "mode_sec": "NCAF"})
        self.assertTrue(ok, err)
        self.assertTrue(cfg.enableaim_sec)
        self.assertEqual(cfg.mode_sec, "NCAF")
        ok, err = server._patch_main_aimbot({"ads_fov_enabled": True, "ads_fovsize": 80})
        self.assertTrue(ok, err)
        self.assertTrue(cfg.ads_fov_enabled)
        self.assertEqual(float(cfg.ads_fovsize), 80.0)
        ok, err = server._patch_sec_aimbot({"ads_fov_enabled_sec": True, "ads_fovsize_sec": 120})
        self.assertTrue(ok, err)
        self.assertTrue(cfg.ads_fov_enabled_sec)
        self.assertEqual(float(cfg.ads_fovsize_sec), 120.0)

        ok, err = server._patch_trigger({"enabletb": True, "trigger_type": "rgb", "trigger_min_ratio": 0.2})
        self.assertTrue(ok, err)
        self.assertTrue(cfg.enabletb)
        self.assertEqual(cfg.trigger_type, "rgb")
        ok, err = server._patch_trigger(
            {
                "tbdelay_min": 0.05,
                "tbdelay_max": 0.2,
                "trigger_ads_fov_enabled": True,
                "trigger_ads_fovsize": 15,
            }
        )
        self.assertTrue(ok, err)
        self.assertTrue(cfg.trigger_ads_fov_enabled)
        self.assertEqual(float(cfg.trigger_ads_fovsize), 15.0)

        ok, err = server._patch_rcs({"enablercs": True, "rcs_pull_speed": 12})
        self.assertTrue(ok, err)
        self.assertTrue(cfg.enablercs)
        self.assertEqual(cfg.rcs_pull_speed, 12)

        ok, err = server._patch_main_aimbot(
            {"anti_smoke_enabled": True, "aimbot_activation_type": "toggle", "selected_mouse_button": 3}
        )
        self.assertTrue(ok, err)
        self.assertTrue(cfg.anti_smoke_enabled)
        self.assertEqual(cfg.aimbot_activation_type, "toggle")
        self.assertEqual(cfg.selected_mouse_button, 3)

        ok, err = server._patch_trigger(
            {
                "tbhold_min": 20,
                "tbhold_max": 40,
                "rgb_color_profile": "custom",
                "trigger_activation_type": "toggle",
                "selected_tb_btn": 4,
            }
        )
        self.assertTrue(ok, err)
        self.assertEqual(float(cfg.tbhold_min), 20.0)
        self.assertEqual(float(cfg.tbhold_max), 40.0)
        self.assertEqual(cfg.rgb_color_profile, "custom")
        self.assertEqual(cfg.trigger_activation_type, "toggle")
        self.assertEqual(cfg.selected_tb_btn, 4)

        ok, err = server._patch_trigger({"tbhold_min": 80, "tbhold_max": 20})
        self.assertFalse(ok)
        self.assertIn("tbhold_min must be <=", err)

    def test_patch_full_state(self):
        cfg, tracker = _build_dummy()
        server = WebMenuServer(cfg, tracker, _DummyCapture(), version_provider=lambda: "1.0.0")

        ok, err = server._patch_full({"color": "red", "normal_x_speed": 11.5})
        self.assertTrue(ok, err)
        self.assertEqual(cfg.color, "red")
        self.assertEqual(float(cfg.normal_x_speed), 11.5)

        ok, err = server._patch_full({"unknown_option": 1})
        self.assertFalse(ok)
        self.assertIn("unknown fields", err)

    def test_configs_save_and_load(self):
        cfg, tracker = _build_dummy()
        server = WebMenuServer(cfg, tracker, _DummyCapture(), version_provider=lambda: "1.0.0")
        with tempfile.TemporaryDirectory() as td:
            server._base_dir = Path(td)
            (server._base_dir / "configs").mkdir(parents=True, exist_ok=True)

            ok, err, name = server._save_new_named_config("my_profile")
            self.assertTrue(ok, err)
            self.assertEqual(name, "my_profile")
            self.assertIn("my_profile", server._list_configs())

            cfg.mode = "Silent"
            ok, err = server._load_named_config("my_profile")
            self.assertTrue(ok, err)
            self.assertEqual(cfg.mode, "Normal")


if __name__ == "__main__":
    unittest.main()
