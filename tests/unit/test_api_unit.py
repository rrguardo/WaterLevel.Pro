import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import api


class FakeRedis:
    def __init__(self, initial=None):
        self.store = dict(initial or {})

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ex=None):
        self.store[key] = str(value)

    def delete(self, key):
        self.store.pop(key, None)


class ApiUnitTestCase(unittest.TestCase):
    def setUp(self):
        self.client = api.app.test_client()

    def test_generate_secure_random_string_complexity(self):
        generated = api.generate_secure_random_string(24)
        self.assertEqual(24, len(generated))
        self.assertTrue(any(char.islower() for char in generated))
        self.assertTrue(any(char.isupper() for char in generated))
        self.assertGreaterEqual(sum(char.isdigit() for char in generated), 3)

    def test_link_without_params_returns_fail(self):
        response = self.client.get("/link")
        self.assertEqual(200, response.status_code)
        self.assertEqual("FAIL", response.get_data(as_text=True))
        self.assertEqual("-", response.headers.get("wpl-key"))

    def test_sensor_view_api_contract(self):
        self.assertTrue(isinstance(api.RELAY_EVENTS_CODE, dict))
        self.assertIn(1, api.RELAY_EVENTS_CODE)
        self.assertIn("Sensor", api.RELAY_EVENTS_CODE[1][1])

    def test_relay_view_api_unknown_action(self):
        response = self.client.post("/relay_view_api", data={"public_key": "x", "action": "noop"})
        payload = response.get_json()
        self.assertEqual(200, response.status_code)
        self.assertEqual("fail unknown action", payload["status"])

    def test_setup_logger_adds_handler(self):
        fake_logger = MagicMock()
        with patch("api.logging.basicConfig") as basic_config, patch("api.logging.getLogger", return_value=fake_logger):
            api.setup_logger()
            basic_config.assert_called_once()
            fake_logger.addHandler.assert_called_once()

    def test_sensor_view_api_with_cached_values(self):
        fake_redis = FakeRedis({"tin-keys/1pubX": "80|1700000000|376|-71"})
        with patch.object(api, "redis_client", fake_redis), patch("api.time.time", return_value=1700000060):
            response = self.client.get("/sensor_view_api", query_string={"public_key": "1pubX"})
            payload = response.get_json()
            self.assertEqual(200, response.status_code)
            self.assertEqual("80", payload["distance"])
            self.assertEqual(60, payload["diff_time"])
            self.assertAlmostEqual(3.76, payload["voltage"])
            self.assertEqual("-71", payload["rssi"])

    def test_relay_view_api_get_consumes_events(self):
        fake_redis = FakeRedis({
            "relay-keys/demorelay": "1|1700000000|-66",
            "relay-events/demorelay": "1,0,4",
        })
        with patch.object(api, "redis_client", fake_redis), patch.object(api.settings, "DEMO_RELAY_PUB_KEY", "demorelay"), patch("api.time.time", return_value=1700000010):
            response = self.client.get("/relay_view_api", query_string={"public_key": "demorelay"})
            payload = response.get_json()
            self.assertEqual(200, response.status_code)
            self.assertEqual(1, payload["status"])
            self.assertEqual(10, payload["diff_time"])
            self.assertTrue(len(payload["events"]) >= 1)
            self.assertIsNone(fake_redis.get("relay-events/demorelay"))

    def test_update_invalid_private_key_returns_404(self):
        with patch("api.db.DevicesDB.valid_private_key", return_value=False):
            response = self.client.get("/update", query_string={"key": "bad", "distance": "80", "voltage": "370"})
            self.assertEqual(404, response.status_code)
            self.assertEqual("invalid private key", response.get_json()["error"])

    def test_update_requires_distance_and_voltage(self):
        with patch("api.db.DevicesDB.valid_private_key", return_value="1pubX"):
            response_missing_distance = self.client.get("/update", query_string={"key": "1prvX", "voltage": "370"})
            response_missing_voltage = self.client.get("/update", query_string={"key": "1prvX", "distance": "80"})
            self.assertEqual("ERROR", response_missing_distance.get_data(as_text=True))
            self.assertEqual("ERROR", response_missing_voltage.get_data(as_text=True))

    def test_update_success_sets_headers_and_cache(self):
        fake_redis = FakeRedis()
        sensor_settings = SimpleNamespace(WIFI_POOL_TIME=45)

        with patch.object(api, "redis_client", fake_redis), \
            patch("api.db.DevicesDB.valid_private_key", return_value="1pubSENSOR"), \
            patch("api.db.DevicesDB.load_device_id_by_public_key", return_value=9), \
            patch("api.db.DevicesDB.record_uptime"), \
            patch("api.db.DevicesDB.load_device_settings", return_value=sensor_settings), \
            patch("api.db.DevicesDB.update_sensor_pool_time") as update_pool, \
            patch("api.time.time", return_value=1700000100):

            response = self.client.get(
                "/update",
                query_string={"key": "1prvSENSOR", "distance": "82", "voltage": "375"},
                headers={"RSSI": "-70", "FW-Version": "10"},
            )

            self.assertEqual(200, response.status_code)
            self.assertEqual("OK", response.get_data(as_text=True))
            self.assertEqual(str(api.LAST_SENSOR_FW_VERSION), response.headers["fw-version"])
            self.assertEqual("45", response.headers["wpl"])
            self.assertEqual("82|1700000100|375|-70", fake_redis.get("tin-keys/1pubSENSOR"))
            update_pool.assert_not_called()

    def test_relay_update_invalid_private_key_returns_404(self):
        with patch("api.db.DevicesDB.valid_private_key", return_value=False):
            response = self.client.get("/relay-update", query_string={"key": "bad", "status": 1})
            self.assertEqual(404, response.status_code)
            self.assertEqual("invalid private key", response.get_json()["error"])

    def test_relay_update_success_headers(self):
        fake_redis = FakeRedis()
        relay_settings = SimpleNamespace(
            SENSOR_KEY="none",
            ALGO=1,
            SAFE_MODE=1,
            START_LEVEL=30,
            END_LEVEL=90,
            AUTO_OFF=1,
            AUTO_ON=1,
            MIN_FLOW_MM_X_MIN=10,
            BLIND_DISTANCE=15,
            HOURS_OFF="1,2",
        )
        with patch.object(api, "redis_client", fake_redis), \
            patch("api.db.DevicesDB.valid_private_key", return_value="3pubR"), \
            patch("api.db.DevicesDB.load_device_id_by_public_key", return_value=20), \
            patch("api.db.DevicesDB.load_device_settings", return_value=relay_settings), \
            patch("api.time.time", return_value=1700000060):
            response = self.client.get(
                "/relay-update",
                query_string={"key": "3prvR", "status": 1},
                headers={"RSSI": "-65", "FW-Version": "11", "EVENTS": "0,0,0,0,0"},
            )
            self.assertEqual(200, response.status_code)
            self.assertEqual("OK", response.get_data(as_text=True))
            self.assertEqual("1", response.headers["ALGO"])
            self.assertEqual("0", response.headers["ACTION"])

    def test_relay_action_helpers(self):
        fake_redis = FakeRedis()
        with patch.object(api, "redis_client", fake_redis):
            self.assertEqual(0, api.get_relay_action("3pubX"))
            api.set_relay_action("3pubX", -1)
            self.assertEqual(-1, api.get_relay_action("3pubX"))

    def test_version_constants_positive(self):
        self.assertGreater(api.LAST_SENSOR_FW_VERSION, 0)
        self.assertGreater(api.LAST_RELAY_FW_VERSION, 0)

    def test_update_persists_history_point(self):
        # Ensure update() calls redis zadd/zremrangebyscore/expire when persisting history
        fake_redis = MagicMock()
        fake_redis.get.return_value = None
        with patch.object(api, 'redis_client', fake_redis), \
            patch('api.db.DevicesDB.valid_private_key', return_value='1pubSENSOR'), \
            patch('api.db.DevicesDB.load_device_id_by_public_key', return_value=9), \
            patch('api.db.DevicesDB.record_uptime'), \
            patch('api.db.DevicesDB.load_device_settings', return_value=SimpleNamespace(EMPTY_LEVEL=100, TOP_MARGIN=0, WIFI_POOL_TIME=30)), \
            patch('api.time.time', return_value=1700000100):

            response = self.client.get('/update', query_string={'key': '1prvSENSOR', 'distance': '80', 'voltage': '375'}, headers={'RSSI':'-70'})
            self.assertEqual(200, response.status_code)
            # zadd should be called to store history point
            self.assertTrue(fake_redis.zadd.called)
            self.assertTrue(fake_redis.zremrangebyscore.called)
            self.assertTrue(fake_redis.expire.called)


if __name__ == "__main__":
    unittest.main()
