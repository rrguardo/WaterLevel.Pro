import unittest

import requests

from tests.integration.docker_integration import load_runtime_settings, start_stack, stop_stack


class AppIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        start_stack()
        cls.runtime = load_runtime_settings()

    @classmethod
    def tearDownClass(cls):
        stop_stack()

    def _get(self, path, params=None, host=None):
        header_host = host or self.runtime["web_host"]
        return requests.get(
            f"{self.runtime['base_url']}{path}",
            params=params,
            headers={"Host": header_host},
            timeout=5,
            verify=False,
            allow_redirects=False,
        )

    def test_http_redirects_to_https(self):
        response = requests.get(
            "http://localhost/ping",
            headers={"Host": self.runtime["web_host"]},
            timeout=5,
            allow_redirects=False,
        )
        self.assertIn(response.status_code, {301, 302, 308})

    def test_ping_endpoint_returns_pong(self):
        response = self._get("/ping")
        self.assertEqual(200, response.status_code)
        self.assertEqual("PONG", response.text)

    def test_index_endpoint_returns_html(self):
        response = self._get("/")
        self.assertEqual(200, response.status_code)
        self.assertIn("text/html", response.headers.get("Content-Type", ""))

    def test_products_and_manuals_routes(self):
        product_response = self._get("/products/WiFi-Water-Level-S1")
        manual_response = self._get("/manuals/WiFi-Smart-Water-Pump-Controller-S1")

        self.assertEqual(200, product_response.status_code)
        self.assertEqual(200, manual_response.status_code)

    def test_short_unknown_redirects_to_root(self):
        response = self._get("/short/unknown")
        self.assertIn(response.status_code, {301, 302})
        self.assertEqual("/", response.headers.get("Location"))

    def test_ipn_route_disabled(self):
        response = self._get("/ipn-routes-83")
        self.assertEqual(410, response.status_code)
        payload = response.json()
        self.assertEqual("disabled", payload["status"])

    def test_data_api_invalid_key(self):
        response = self._get("/data-api", params={"key": "missing"})
        self.assertEqual(404, response.status_code)
        self.assertEqual("invalid key", response.json()["error"])

    def test_set_language_sets_cookie(self):
        response = requests.get(
            f"{self.runtime['base_url']}/set_language/es",
            headers={"Host": self.runtime["web_host"], "Referer": f"{self.runtime['base_url']}/"},
            timeout=5,
            verify=False,
            allow_redirects=False,
        )
        self.assertIn(response.status_code, {301, 302})
        self.assertIn("lang=es", response.headers.get("Set-Cookie", ""))

    def test_static_assets_routes(self):
        robots = self._get("/robots.txt")
        sitemap = self._get("/sitemap.xml")
        image_sitemap = self._get("/image-sitemap.xml")
        ads_lower = self._get("/ads.txt")
        ads_upper = self._get("/Ads.txt")

        self.assertEqual(200, robots.status_code)
        self.assertEqual(200, sitemap.status_code)
        self.assertEqual(200, image_sitemap.status_code)
        self.assertEqual(200, ads_lower.status_code)
        self.assertEqual(200, ads_upper.status_code)


if __name__ == "__main__":
    unittest.main()
