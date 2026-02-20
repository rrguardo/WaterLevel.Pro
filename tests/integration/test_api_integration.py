import time
import unittest

import requests

from tests.integration.docker_integration import load_runtime_settings, start_stack, stop_stack


class ApiIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        start_stack()
        cls.runtime = load_runtime_settings()

    @classmethod
    def tearDownClass(cls):
        stop_stack()

    def _get(self, path, params=None, headers=None):
        request_headers = {"Host": self.runtime["api_host"]}
        if headers:
            request_headers.update(headers)

        last_exc = None
        for _ in range(3):
            try:
                return requests.get(
                    f"{self.runtime['base_url']}{path}",
                    params=params,
                    headers=request_headers,
                    timeout=5,
                    verify=False,
                )
            except requests.RequestException as ex:
                last_exc = ex
                time.sleep(1)
        raise last_exc

    def _post(self, path, data=None, headers=None):
        request_headers = {"Host": self.runtime["api_host"]}
        if headers:
            request_headers.update(headers)

        last_exc = None
        for _ in range(3):
            try:
                return requests.post(
                    f"{self.runtime['base_url']}{path}",
                    data=data,
                    headers=request_headers,
                    timeout=5,
                    verify=False,
                )
            except requests.RequestException as ex:
                last_exc = ex
                time.sleep(1)
        raise last_exc

    def test_api_cors_header_for_allowed_origin(self):
        response = self._get("/sensor_view_api", params={"public_key": "demo"}, headers={"Origin": self.runtime["app_domain"]})
        self.assertEqual(200, response.status_code)
        self.assertEqual(self.runtime["app_domain"], response.headers.get("Access-Control-Allow-Origin"))

    def test_api_link_without_params_returns_fail(self):
        response = self._get("/link")
        self.assertEqual(200, response.status_code)
        self.assertEqual("FAIL", response.text)
        self.assertIn("fw-version", response.headers)
        self.assertEqual("-", response.headers.get("wpl-key"))

    def test_api_link_unknown_email_stays_fail(self):
        random_email = f"no-user-{int(time.time())}@example.local"
        response = self._get("/link", params={"email": random_email, "key": "-", "dtype": "1"})
        self.assertEqual(200, response.status_code)
        self.assertEqual("FAIL", response.text)

    def test_sensor_view_api_returns_json_contract(self):
        response = self._get("/sensor_view_api", params={"public_key": "demo"})
        payload = response.json()
        self.assertEqual(200, response.status_code)
        self.assertIn("distance", payload)
        self.assertIn("rtime", payload)
        self.assertIn("voltage", payload)
        self.assertIn("diff_time", payload)
        self.assertIn("skey", payload)

    def test_update_valid_private_key_missing_distance_returns_error(self):
        response = self._get(
            "/update",
            params={"key": self.runtime["demo_s1_prv_key"], "voltage": "370"},
            headers={"RSSI": "-65", "FW-Version": "22"},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("ERROR", response.text)

    def test_update_valid_private_key_missing_voltage_returns_error(self):
        response = self._get(
            "/update",
            params={"key": self.runtime["demo_s1_prv_key"], "distance": "90"},
            headers={"RSSI": "-65", "FW-Version": "22"},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("ERROR", response.text)

    def test_update_success_and_sensor_view_reflects_data(self):
        update_response = self._get(
            "/update",
            params={"key": self.runtime["demo_s1_prv_key"], "distance": "88", "voltage": "377"},
            headers={"RSSI": "-62", "FW-Version": "22"},
        )
        self.assertEqual(200, update_response.status_code)
        self.assertEqual("OK", update_response.text)
        self.assertIn("wpl", update_response.headers)
        self.assertIn("fw-version", update_response.headers)

        sensor_response = self._get("/sensor_view_api", params={"public_key": "demo"})
        sensor_payload = sensor_response.json()
        self.assertEqual(200, sensor_response.status_code)
        self.assertTrue(str(sensor_payload["distance"]).isdigit())
        self.assertEqual(self.runtime["demo_s1_pub_key"], sensor_payload["skey"])

    def test_relay_view_api_get_returns_json_contract(self):
        response = self._get("/relay_view_api", params={"public_key": "demorelay"})
        payload = response.json()
        self.assertEqual(200, response.status_code)
        self.assertIn("status", payload)
        self.assertIn("rtime", payload)
        self.assertIn("diff_time", payload)
        self.assertIn("rssi", payload)
        self.assertIn("events", payload)

    def test_relay_view_api_post_unknown_action_rejected(self):
        response = self._post("/relay_view_api", data={"public_key": "demorelay", "action": "noop"})
        self.assertEqual(200, response.status_code)
        self.assertEqual("fail unknown action", response.json()["status"])

    def test_relay_view_api_post_accepts_action(self):
        response = self._post("/relay_view_api", data={"public_key": "demorelay", "action": "on"})
        self.assertEqual(200, response.status_code)
        self.assertEqual("success", response.json()["status"])

    def test_relay_update_success_sets_runtime_headers(self):
        response = self._get(
            "/relay-update",
            params={"key": self.runtime["demo_relay_prv_key"], "status": "1"},
            headers={"RSSI": "-61", "FW-Version": "19", "EVENTS": "0,0,0,0,0"},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("OK", response.text)
        self.assertIn("ALGO", response.headers)
        self.assertIn("ACTION", response.headers)
        self.assertIn("pool-time", response.headers)
        self.assertIn("fw-version", response.headers)

    def test_relay_update_events_then_relay_view_consumes_events(self):
        response_update = self._get(
            "/relay-update",
            params={"key": self.runtime["demo_relay_prv_key"], "status": "1"},
            headers={"RSSI": "-60", "FW-Version": "19", "EVENTS": "1,2,0,0,0"},
        )
        self.assertEqual(200, response_update.status_code)

        response_view_1 = self._get("/relay_view_api", params={"public_key": "demorelay"})
        self.assertTrue(len(response_view_1.json()["events"]) >= 1)

        response_view_2 = self._get("/relay_view_api", params={"public_key": "demorelay"})
        self.assertEqual([], response_view_2.json()["events"])

    def test_relay_action_flow_on_then_off(self):
        response_on = self._post("/relay_view_api", data={"public_key": self.runtime["demo_relay_pub_key"], "action": "on"})
        self.assertEqual("success", response_on.json()["status"])

        response_update_on = self._get(
            "/relay-update",
            params={"key": self.runtime["demo_relay_prv_key"], "status": "1"},
            headers={"RSSI": "-59", "FW-Version": "19", "EVENTS": "0,0,0,0,0"},
        )
        self.assertEqual("1", response_update_on.headers.get("ACTION"))

        response_off = self._post("/relay_view_api", data={"public_key": self.runtime["demo_relay_pub_key"], "action": "off"})
        self.assertEqual("success", response_off.json()["status"])

        response_update_off = self._get(
            "/relay-update",
            params={"key": self.runtime["demo_relay_prv_key"], "status": "1"},
            headers={"RSSI": "-58", "FW-Version": "19", "EVENTS": "0,0,0,0,0"},
        )
        self.assertEqual("-1", response_update_off.headers.get("ACTION"))

        response_update_reset = self._get(
            "/relay-update",
            params={"key": self.runtime["demo_relay_prv_key"], "status": "1"},
            headers={"RSSI": "-58", "FW-Version": "19", "EVENTS": "0,0,0,0,0"},
        )
        self.assertEqual("0", response_update_reset.headers.get("ACTION"))

    def test_update_invalid_private_key_returns_404(self):
        response = self._get("/update", params={"key": "invalid-key", "distance": "80", "voltage": "370"})
        self.assertEqual(404, response.status_code)
        self.assertEqual("invalid private key", response.json()["error"])

    def test_relay_update_invalid_private_key_returns_404(self):
        response = self._get("/relay-update", params={"key": "invalid-key", "status": "1"})
        self.assertEqual(404, response.status_code)
        self.assertEqual("invalid private key", response.json()["error"])


if __name__ == "__main__":
    unittest.main()
