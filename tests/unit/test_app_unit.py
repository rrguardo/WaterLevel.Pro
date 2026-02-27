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


class AppUnitTestCase(unittest.TestCase):
    def setUp(self):
        self.app = web_app.app
        self.app.config["TESTING"] = True
        self.app.config["LOGIN_DISABLED"] = True
        self.client = web_app.app.test_client()
        self.original_redis = web_app.redis_client
        web_app.redis_client = FakeRedis()

    def tearDown(self):
        web_app.redis_client = self.original_redis

    def test_generate_secure_random_string_complexity(self):
        generated = web_app.generate_secure_random_string(20)
        self.assertEqual(20, len(generated))
        self.assertTrue(any(char.islower() for char in generated))
        self.assertTrue(any(char.isupper() for char in generated))
        self.assertGreaterEqual(sum(char.isdigit() for char in generated), 3)

    def test_format_hours_and_event_text(self):
        self.assertEqual("2 days and 3 hours", web_app.format_hours(51))
        self.assertEqual("0 hours", web_app.format_hours(0))
        self.assertIn("Sensor", web_app.get_relay_event_text(1))

    def test_process_ipn_returns_false(self):
        self.assertFalse(web_app.process_ipn({"txn_id": "abc"}))

    def test_ping_endpoint(self):
        response = self.client.get("/ping")
        self.assertEqual(200, response.status_code)
        self.assertEqual("PONG", response.get_data(as_text=True))

    def test_short_unknown_redirects(self):
        response = self.client.get("/short/unknown")
        self.assertIn(response.status_code, {301, 302})
        self.assertTrue(response.location.endswith("/"))

    def test_set_language_sets_cookie(self):
        response = self.client.get("/set_language/es", headers={"Referer": "/"})
        self.assertIn(response.status_code, {301, 302})
        self.assertIn("lang=es", response.headers.get("Set-Cookie", ""))

    def test_setup_logger_adds_handler(self):
        fake_logger = MagicMock()
        with patch("app.logging.basicConfig") as basic_config, patch("app.logging.getLogger", return_value=fake_logger):
            web_app.setup_logger()
            basic_config.assert_called_once()
            fake_logger.addHandler.assert_called_once()

    def test_get_locale_defaults_and_invalid_fallback(self):
        with self.app.test_request_context("/", method="GET"):
            web_app.request.view_args = {}
            self.assertEqual("en", web_app.get_locale())

        with self.app.test_request_context("/xx", method="GET"):
            web_app.request.view_args = {"lang": "xx"}
            self.assertEqual("en", web_app.get_locale())

    def test_ensure_language_redirect(self):
        @web_app.ensure_language
        def wrapped(lang="en"):
            return "OK"

        with self.app.test_request_context("/es/devices?x=1", method="GET", headers={"Cookie": "lang=hi"}):
            response = wrapped(lang="es")
            self.assertEqual(302, response.status_code)

    def test_validate_recaptcha_success(self):
        fake_response = MagicMock()
        fake_response.json.return_value = {"success": True}
        with patch("app.requests.post", return_value=fake_response):
            self.assertTrue(web_app.validate_recaptcha("token"))

    def test_get_device_data_success(self):
        web_app.redis_client.set("tin-keys/pub1", "99|1700000000|380|-69")
        web_app.redis_client.set("tin-sett-keys/pub1", "120|20|30")
        with patch("app.time.time", return_value=1700000030):
            response = self.client.get("/data-api", query_string={"key": "pub1"})
            payload = response.get_json()
            self.assertEqual(200, response.status_code)
            self.assertEqual("99", payload["distance"])
            self.assertEqual(3.8, payload["voltage"])

    def test_get_device_data_demo_alias(self):
        # Ensure demo alias maps to configured demo public key
        demo_pub = "1pubDEMO_TEST"
        web_app.redis_client.set(f"tin-keys/{demo_pub}", "50|1700000000|370|-65")
        with patch.object(web_app.settings, "DEMO_S1_PUB_KEY", demo_pub):
            with patch("app.time.time", return_value=1700000030):
                response = self.client.get("/data-api", query_string={"key": "demo"})
                payload = response.get_json()
                self.assertEqual(200, response.status_code)
                self.assertEqual("50", payload["distance"])
                self.assertAlmostEqual(3.7, payload["voltage"])

    def test_sensor_stats_endpoint_unit(self):
        # Patch redis zrangebyscore to return sample entries for aggregation
        demo_pub = "1pubDEMO_TEST"
        sample_items = ["60|3.8"]
        fake_redis = web_app.redis_client
        def fake_zrange(key, lo, hi):
            return sample_items

        with patch.object(web_app, 'redis_client') as rc:
            rc.zrangebyscore = MagicMock(side_effect=fake_zrange)
            with patch.object(web_app.settings, 'DEMO_S1_PUB_KEY', demo_pub):
                with patch('app.time.time', return_value=1700003600):
                    response = self.client.get('/sensor_stats', query_string={'public_key': 'demo'})
                    self.assertEqual(200, response.status_code)
                    payload = response.get_json()
                    self.assertIn('buckets', payload)
                    self.assertEqual(24, len(payload['buckets']))
                    # first bucket should contain averaged values
                    first = payload['buckets'][0]
                    self.assertFalse(first.get('offline'))
                    self.assertEqual(60.0, first.get('percent'))
                    self.assertEqual(3.8, first.get('voltage'))

    def test_devices_post_paths(self):
        with patch.object(web_app, "current_user", SimpleNamespace(is_authenticated=False)):
            response_fail = self.client.post("/devices", data={"action": "add", "public_key": "1pubX"})
            self.assertEqual("fail", response_fail.get_json()["status"])

        fake_user = SimpleNamespace(is_authenticated=True, add_device=MagicMock(), remove_device=MagicMock())
        with patch.object(web_app, "current_user", fake_user):
            response_add = self.client.post("/devices", data={"action": "add", "public_key": "1pubX", "name": "mydev"})
            response_remove = self.client.post("/devices", data={"action": "remove", "public_key": "1pubX"})
            self.assertEqual("success", response_add.get_json()["status"])
            self.assertEqual("success", response_remove.get_json()["status"])

    def test_login_post_invalid_recaptcha(self):
        with patch("app.validate_recaptcha", return_value=False):
            response = self.client.post("/login", data={"email": "u@example.com", "password": "pass", "g-recaptcha-response": "bad"})
            self.assertEqual(200, response.status_code)

    def test_register_post_invalid_email(self):
        with patch("app.validate_recaptcha", return_value=True), patch("app.validate_email", side_effect=web_app.EmailNotValidError("bad")):
            response = self.client.post("/register", data={"email": "bad", "password": "pass", "g-recaptcha-response": "ok"})
            self.assertEqual(200, response.status_code)

    def test_before_request_sets_img_lang(self):
        with self.app.test_request_context("/es"):
            web_app.request.view_args = {"lang": "es"}
            web_app.before_request()
            self.assertEqual("es", web_app.g.lang)
            self.assertEqual("_es", web_app.g.img_lang)

    def test_get_timezone_uses_g_user(self):
        with self.app.test_request_context("/"):
            web_app.g.user = SimpleNamespace(timezone="UTC")
            self.assertEqual("UTC", web_app.get_timezone())

    def test_inject_global_variables_contact_pending_true(self):
        web_app.redis_client.set("users_support", "2")
        result = web_app.inject_global_variables()
        self.assertEqual(True, result["CONTACT_PENDING"])
        self.assertIn("TRACKING_CONFIG", result)

    def test_utility_processor_url_with_lang(self):
        with self.app.test_request_context("/es/devices"):
            web_app.g.lang = "es"
            helper = web_app.utility_processor()["url_with_lang"]
            self.assertEqual("/es/devices", helper("devices"))

    def test_load_user_from_db(self):
        fake_row = SimpleNamespace(id=1, email="u@example.com", passw="h", is_admin=0)
        fake_user = object()
        with patch("app.db.get_user_by_id", return_value=fake_row), patch("app.db.User", return_value=fake_user):
            self.assertIs(fake_user, web_app.load_user(1))

    def test_admin_login_required_allows_when_login_disabled(self):
        self.app.config["LOGIN_DISABLED"] = True

        @web_app.admin_login_required
        def sample():
            return "PASS"

        with self.app.test_request_context("/reportes/x"):
            self.assertEqual("PASS", sample())

    def test_get_device_data_invalid_key(self):
        response = self.client.get("/data-api", query_string={"key": "missing"})
        self.assertEqual(404, response.status_code)

    def test_login_post_success(self):
        fake_row = SimpleNamespace(
            id=3,
            email="u@example.com",
            passw=web_app.hashlib.sha256("pass".encode()).hexdigest(),
            is_admin=0,
            confirmed=1,
        )
        with patch("app.validate_recaptcha", return_value=True), \
            patch("app.db.try_login", return_value=fake_row), \
            patch("app.db.User", return_value=SimpleNamespace(id=3)), \
            patch("app.login_user"):
            response = self.client.post(
                "/login",
                data={"email": "u@example.com", "password": "pass", "g-recaptcha-response": "ok", "remember": "on"},
                follow_redirects=False,
            )
            self.assertEqual(302, response.status_code)

    def test_register_post_success(self):
        valid_email_obj = SimpleNamespace(email="valid@example.com")
        with patch("app.validate_recaptcha", return_value=True), \
            patch("app.validate_email", return_value=valid_email_obj), \
            patch("app.db.valid_4register", return_value=True), \
            patch("app.db.add_user", return_value=True), \
            patch("app.email_tools.send_register_email") as send_register_email:
            response = self.client.post(
                "/register",
                data={"email": "valid@example.com", "password": "pass", "g-recaptcha-response": "ok"},
            )
            self.assertEqual(200, response.status_code)
            send_register_email.assert_called_once()

    def test_user_confirm_paths(self):
        with patch("app.email_tools.check_confirmation_code", return_value=True), patch("app.db.confirm_user") as confirm_user:
            response_ok = self.client.get("/user-confirm", query_string={"email": "u@example.com", "code": "abc"})
            self.assertEqual(200, response_ok.status_code)
            confirm_user.assert_called_once()

        with patch("app.email_tools.check_confirmation_code", return_value=False), patch("app.db.confirm_user") as confirm_user:
            response_bad = self.client.get("/user-confirm", query_string={"email": "u@example.com", "code": "bad"})
            self.assertEqual(200, response_bad.status_code)
            confirm_user.assert_not_called()

    def test_products_manuals_and_ipn_routes(self):
        response_products = self.client.get("/products/WiFi-Water-Level-S1")
        response_products_redirect = self.client.get("/products/WiFi-Water-Level-S2")
        response_manuals = self.client.get("/manuals/WiFi-Smart-Water-Pump-Controller-S1")
        response_ipn = self.client.get("/ipn-routes-83")

        self.assertEqual(200, response_products.status_code)
        self.assertIn(response_products_redirect.status_code, {301, 302})
        self.assertEqual(200, response_manuals.status_code)
        self.assertEqual(410, response_ipn.status_code)

    def test_contact_post_authenticated(self):
        auth_user = SimpleNamespace(is_authenticated=True, username="u@example.com")
        with patch.object(web_app, "current_user", auth_user), \
            patch("app.validate_recaptcha", return_value=True), \
            patch("app.validate_email", return_value=SimpleNamespace(email="u@example.com")), \
            patch("app.db.Support.add_user_support_record") as add_support:
            response = self.client.post(
                "/contact",
                data={
                    "reason": "help",
                    "device_type": "s1",
                    "g-recaptcha-response": "ok",
                    "email": "u@example.com",
                    "message": "Need support",
                },
            )
            self.assertEqual(200, response.status_code)
            add_support.assert_called_once()


if __name__ == "__main__":
    unittest.main()
