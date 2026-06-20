import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import app as web_app


class FakeRedis:
    def __init__(self, initial=None):
        self.store = dict(initial or {})

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ex=None):
        self.store[key] = str(value)

    def incr(self, key):
        value = int(self.store.get(key, 0)) + 1
        self.store[key] = str(value)
        return value

    def delete(self, key):
        self.store.pop(key, None)

    def expire(self, key, seconds):
        return True

    def flushall(self):
        self.store.clear()


class MobileApiUnitTestCase(unittest.TestCase):
    def setUp(self):
        self.app = web_app.app
        self.app.config["TESTING"] = True
        self.app.config["LOGIN_DISABLED"] = True
        self.client = web_app.app.test_client()
        self.original_redis = web_app.redis_client
        web_app.redis_client = FakeRedis()

    def tearDown(self):
        web_app.redis_client = self.original_redis

    def _fake_user(self, **overrides):
        email = overrides.pop("email", "user@example.com")
        attrs = dict(
            id=1,
            username=email,
            is_admin=False,
            is_authenticated=True,
            get_devices=lambda: [],
            set_setting=MagicMock(),
        )
        attrs.update(overrides)
        return SimpleNamespace(**attrs)

    # ── /login ──────────────────────────────────────────────────

    def test_login_missing_body_returns_400(self):
        response = self.client.post("/users-api-mobile/login", content_type="application/json")
        self.assertEqual(400, response.status_code)
        self.assertIn("error", response.get_json())

    def test_login_missing_fields_returns_400(self):
        response = self.client.post("/users-api-mobile/login", json={"email": "", "password": ""})
        self.assertEqual(400, response.status_code)

    def test_login_dev_mode_skips_recaptcha_success(self):
        fake_row = SimpleNamespace(
            id=1, email="user@example.com",
            passw=web_app.hashlib.sha256("pass".encode()).hexdigest(),
            is_admin=0, confirmed=1,
        )
        with patch("mobile_api.settings.DEV_MODE", True), \
            patch("mobile_api.db.try_login", return_value=fake_row), \
            patch("mobile_api.db.User", return_value=SimpleNamespace(id=1)), \
            patch("mobile_api.login_user") as login_user:
            response = self.client.post("/users-api-mobile/login", json={
                "email": "user@example.com", "password": "pass",
            })
            self.assertEqual(200, response.status_code)
            payload = response.get_json()
            self.assertTrue(payload["success"])
            self.assertEqual(1, payload["user"]["id"])
            login_user.assert_called_once()

    def test_login_dev_mode_missing_password_returns_400(self):
        with patch("mobile_api.settings.DEV_MODE", True):
            response = self.client.post("/users-api-mobile/login", json={"email": "user@example.com"})
            self.assertEqual(400, response.status_code)

    def test_login_dev_mode_invalid_credentials_returns_401(self):
        with patch("mobile_api.settings.DEV_MODE", True), \
            patch("mobile_api.db.try_login", return_value=None):
            response = self.client.post("/users-api-mobile/login", json={
                "email": "user@example.com", "password": "wrong",
            })
            self.assertEqual(401, response.status_code)
            self.assertIn("error", response.get_json())

    def test_login_dev_mode_unconfirmed_returns_403(self):
        fake_row = SimpleNamespace(
            id=1, email="user@example.com",
            passw=web_app.hashlib.sha256("pass".encode()).hexdigest(),
            is_admin=0, confirmed=0,
        )
        with patch("mobile_api.settings.DEV_MODE", True), \
            patch("mobile_api.db.try_login", return_value=fake_row):
            response = self.client.post("/users-api-mobile/login", json={
                "email": "user@example.com", "password": "pass",
            })
            self.assertEqual(403, response.status_code)
            self.assertIn("not confirmed", response.get_json()["error"].lower())

    def test_login_recaptcha_required_in_production(self):
        with patch("mobile_api.settings.DEV_MODE", False):
            response = self.client.post("/users-api-mobile/login", json={
                "email": "user@example.com", "password": "pass",
            })
            self.assertEqual(400, response.status_code)
            self.assertIn("recaptcha_token", response.get_json()["error"].lower())

    def test_login_recaptcha_failure_returns_403(self):
        with patch("mobile_api.settings.DEV_MODE", False), \
            patch("mobile_api._validate_recaptcha", return_value=False):
            response = self.client.post("/users-api-mobile/login", json={
                "email": "user@example.com", "password": "pass",
                "recaptcha_token": "bad",
            })
            self.assertEqual(403, response.status_code)
            self.assertIn("recaptcha", response.get_json()["error"].lower())

    def test_login_recaptcha_success_production(self):
        fake_row = SimpleNamespace(
            id=2, email="u@example.com",
            passw=web_app.hashlib.sha256("p".encode()).hexdigest(),
            is_admin=1, confirmed=1,
        )
        with patch("mobile_api.settings.DEV_MODE", False), \
            patch("mobile_api._validate_recaptcha", return_value=True), \
            patch("mobile_api.db.try_login", return_value=fake_row), \
            patch("mobile_api.db.User", return_value=SimpleNamespace(id=2)), \
            patch("mobile_api.login_user"):
            response = self.client.post("/users-api-mobile/login", json={
                "email": "u@example.com", "password": "p",
                "recaptcha_token": "good",
            })
            self.assertEqual(200, response.status_code)
            self.assertTrue(response.get_json()["success"])

    # ── /register ───────────────────────────────────────────────

    def test_register_dev_mode_skips_recaptcha_success(self):
        with patch("mobile_api.settings.DEV_MODE", True), \
            patch("mobile_api.validate_email", return_value=SimpleNamespace(email="new@example.com")), \
            patch("mobile_api.db.valid_4register", return_value=True), \
            patch("mobile_api.db.add_user", return_value=True), \
            patch("mobile_api.email_tools.send_register_email") as send_email:
            response = self.client.post("/users-api-mobile/register", json={
                "email": "new@example.com", "password": "pass",
            })
            self.assertEqual(201, response.status_code)
            self.assertTrue(response.get_json()["success"])
            send_email.assert_called_once()

    def test_register_missing_body_returns_400(self):
        response = self.client.post("/users-api-mobile/register", content_type="application/json")
        self.assertEqual(400, response.status_code)

    def test_register_invalid_email_returns_400(self):
        with patch("mobile_api.settings.DEV_MODE", True), \
            patch("mobile_api.validate_email", side_effect=web_app.EmailNotValidError("bad")):
            response = self.client.post("/users-api-mobile/register", json={
                "email": "bad", "password": "pass",
            })
            self.assertEqual(400, response.status_code)

    def test_register_duplicate_email_returns_409(self):
        with patch("mobile_api.settings.DEV_MODE", True), \
            patch("mobile_api.validate_email", return_value=SimpleNamespace(email="dup@example.com")), \
            patch("mobile_api.db.valid_4register", return_value=False):
            response = self.client.post("/users-api-mobile/register", json={
                "email": "dup@example.com", "password": "pass",
            })
            self.assertEqual(409, response.status_code)

    def test_register_recaptcha_required_in_production(self):
        with patch("mobile_api.settings.DEV_MODE", False):
            response = self.client.post("/users-api-mobile/register", json={
                "email": "new@example.com", "password": "pass",
            })
            self.assertEqual(400, response.status_code)
            self.assertIn("recaptcha_token", response.get_json()["error"].lower())

    def test_register_recaptcha_failure_returns_403(self):
        with patch("mobile_api.settings.DEV_MODE", False), \
            patch("mobile_api._validate_recaptcha", return_value=False):
            response = self.client.post("/users-api-mobile/register", json={
                "email": "new@example.com", "password": "pass",
                "recaptcha_token": "bad",
            })
            self.assertEqual(403, response.status_code)

    def test_register_recaptcha_success_production(self):
        with patch("mobile_api.settings.DEV_MODE", False), \
            patch("mobile_api._validate_recaptcha", return_value=True), \
            patch("mobile_api.validate_email", return_value=SimpleNamespace(email="new@example.com")), \
            patch("mobile_api.db.valid_4register", return_value=True), \
            patch("mobile_api.db.add_user", return_value=True), \
            patch("mobile_api.email_tools.send_register_email"):
            response = self.client.post("/users-api-mobile/register", json={
                "email": "new@example.com", "password": "pass",
                "recaptcha_token": "good",
            })
            self.assertEqual(201, response.status_code)
            self.assertTrue(response.get_json()["success"])

    # ── /me ─────────────────────────────────────────────────────

    def test_me_authenticated(self):
        fake_user = self._fake_user(id=5, email="me@example.com", is_admin=True)
        with patch("mobile_api.current_user", fake_user), \
            patch("mobile_api.db.get_user_by_id", return_value=SimpleNamespace(phone=1234567890)):
            response = self.client.get("/users-api-mobile/me")
            self.assertEqual(200, response.status_code)
            payload = response.get_json()
            self.assertEqual(5, payload["user"]["id"])
            self.assertEqual("me@example.com", payload["user"]["email"])
            self.assertTrue(payload["user"]["is_admin"])
            self.assertEqual(1234567890, payload["user"]["phone"])

    def test_me_authenticated_no_phone(self):
        fake_user = self._fake_user(id=5, email="me@example.com")
        with patch("mobile_api.current_user", fake_user), \
            patch("mobile_api.db.get_user_by_id", return_value=SimpleNamespace(phone=None)):
            response = self.client.get("/users-api-mobile/me")
            self.assertEqual(200, response.status_code)
            self.assertIsNone(response.get_json()["user"]["phone"])

    def test_me_unauthenticated_returns_401(self):
        self.app.config["LOGIN_DISABLED"] = False
        response = self.client.get("/users-api-mobile/me")
        self.assertEqual(401, response.status_code)
        self.assertIn("Authentication required", response.get_json()["error"])

    # ── /logout ─────────────────────────────────────────────────

    def test_logout_authenticated(self):
        fake_user = self._fake_user(id=1)
        with patch("mobile_api.current_user", fake_user), \
            patch("mobile_api.logout_user") as logout_user:
            response = self.client.post("/users-api-mobile/logout")
            self.assertEqual(200, response.status_code)
            self.assertTrue(response.get_json()["success"])
            logout_user.assert_called_once()

    def test_logout_unauthenticated_returns_401(self):
        self.app.config["LOGIN_DISABLED"] = False
        response = self.client.post("/users-api-mobile/logout")
        self.assertEqual(401, response.status_code)

    # ── /devices ────────────────────────────────────────────────

    def test_devices_authenticated_empty(self):
        fake_user = self._fake_user(id=1, get_devices=lambda: [])
        with patch("mobile_api.current_user", fake_user):
            response = self.client.get("/users-api-mobile/devices")
            self.assertEqual(200, response.status_code)
            self.assertEqual([], response.get_json()["devices"])

    def test_devices_authenticated_with_devices(self):
        fake_devices = [
            SimpleNamespace(public_key="1pubS1", name="Pool Sensor", type=1, long_name="Water Level Sensor S1", can_admin=1),
            SimpleNamespace(public_key="3pubR1", name="Pump Relay", type=3, long_name="Smart Pump Controller R1", can_admin=0),
        ]
        fake_user = self._fake_user(id=1, get_devices=lambda: fake_devices)
        with patch("mobile_api.current_user", fake_user):
            response = self.client.get("/users-api-mobile/devices")
            self.assertEqual(200, response.status_code)
            devices = response.get_json()["devices"]
            self.assertEqual(2, len(devices))
            self.assertEqual("1pubS1", devices[0]["public_key"])
            self.assertEqual("Pool Sensor", devices[0]["name"])
            self.assertEqual(1, devices[0]["type"])
            self.assertTrue(devices[0]["can_admin"])
            self.assertEqual("3pubR1", devices[1]["public_key"])
            self.assertFalse(devices[1]["can_admin"])

    def test_devices_unauthenticated_returns_401(self):
        self.app.config["LOGIN_DISABLED"] = False
        response = self.client.get("/users-api-mobile/devices")
        self.assertEqual(401, response.status_code)

    # ── /settings GET ───────────────────────────────────────────

    def test_settings_get_authenticated(self):
        fake_settings = {"email-alert": "on", "frequency-alert": "30", "sms-alert": "off"}
        fake_user = self._fake_user(id=1)
        with patch("mobile_api.current_user", fake_user), \
            patch("mobile_api.db.User.get_user_settings", return_value=fake_settings):
            response = self.client.get("/users-api-mobile/settings")
            self.assertEqual(200, response.status_code)
            self.assertEqual(fake_settings, response.get_json()["settings"])

    def test_settings_get_unauthenticated_returns_401(self):
        self.app.config["LOGIN_DISABLED"] = False
        response = self.client.get("/users-api-mobile/settings")
        self.assertEqual(401, response.status_code)

    # ── /settings PUT ───────────────────────────────────────────

    def test_settings_put_authenticated(self):
        set_setting = MagicMock()
        fake_user = self._fake_user(id=1, set_setting=set_setting)
        with patch("mobile_api.current_user", fake_user):
            response = self.client.put("/users-api-mobile/settings", json={
                "setting_name": "email-alert", "setting_value": "on",
            })
            self.assertEqual(200, response.status_code)
            self.assertTrue(response.get_json()["success"])
            set_setting.assert_called_once_with("email-alert", "on")

    def test_settings_put_missing_name_returns_400(self):
        fake_user = self._fake_user(id=1)
        with patch("mobile_api.current_user", fake_user):
            response = self.client.put("/users-api-mobile/settings", json={
                "setting_value": "on",
            })
            self.assertEqual(400, response.status_code)
            self.assertIn("setting_name", response.get_json()["error"].lower())

    def test_settings_put_invalid_body_returns_400(self):
        fake_user = self._fake_user(id=1)
        with patch("mobile_api.current_user", fake_user):
            response = self.client.put("/users-api-mobile/settings", content_type="application/json", data="not json")
            self.assertEqual(400, response.status_code)

    def test_settings_put_unauthenticated_returns_401(self):
        self.app.config["LOGIN_DISABLED"] = False
        response = self.client.put("/users-api-mobile/settings", json={
            "setting_name": "email-alert", "setting_value": "on",
        })
        self.assertEqual(401, response.status_code)

    # ── login remember flag ────────────────────────────────────

    def test_login_passes_remember_to_login_user(self):
        fake_row = SimpleNamespace(
            id=1, email="u@example.com",
            passw=web_app.hashlib.sha256("p".encode()).hexdigest(),
            is_admin=0, confirmed=1,
        )
        with patch("mobile_api.settings.DEV_MODE", True), \
            patch("mobile_api.db.try_login", return_value=fake_row), \
            patch("mobile_api.db.User", return_value=SimpleNamespace(id=1)), \
            patch("mobile_api.login_user") as login_user:
            self.client.post("/users-api-mobile/login", json={
                "email": "u@example.com", "password": "p", "remember": True,
            })
            login_user.assert_called_once_with(SimpleNamespace(id=1), remember=True)

    def test_login_remember_defaults_false(self):
        fake_row = SimpleNamespace(
            id=1, email="u@example.com",
            passw=web_app.hashlib.sha256("p".encode()).hexdigest(),
            is_admin=0, confirmed=1,
        )
        with patch("mobile_api.settings.DEV_MODE", True), \
            patch("mobile_api.db.try_login", return_value=fake_row), \
            patch("mobile_api.db.User", return_value=SimpleNamespace(id=1)), \
            patch("mobile_api.login_user") as login_user:
            self.client.post("/users-api-mobile/login", json={
                "email": "u@example.com", "password": "p",
            })
            login_user.assert_called_once_with(SimpleNamespace(id=1), remember=False)


if __name__ == "__main__":
    unittest.main()
