import argparse
import math
import os
import random
import signal
import sys
import time

import requests
import urllib3


class S1DemoDeviceService:
    def __init__(self, args):
        self.base_url = args.base_url.rstrip("/")
        self.update_url = f"{self.base_url}/update"
        self.public_key = args.public_key
        self.private_key = args.private_key
        self.fw_version = args.fw_version
        self.timeout = args.timeout
        self.verify_tls = args.verify_tls
        self.host_header = args.host_header

        self.default_interval = max(1, args.interval)
        self.current_interval = self.default_interval

        self.distance_min = args.distance_min
        self.distance_max = args.distance_max
        self.distance_jitter = max(0, args.distance_jitter)
        self.wave_period = max(1, args.wave_period)

        self.voltage_base = args.voltage_base
        self.voltage_jitter = max(0.0, args.voltage_jitter)

        self.rssi_base = args.rssi_base
        self.rssi_jitter = max(0, args.rssi_jitter)

        self.running = True
        self.start_time = time.time()

    def _build_distance_cm(self):
        center = (self.distance_min + self.distance_max) / 2.0
        amplitude = (self.distance_max - self.distance_min) / 2.0
        elapsed = max(0.0, time.time() - self.start_time)
        wave = math.sin((2.0 * math.pi * elapsed) / self.wave_period)
        noise = random.uniform(-self.distance_jitter, self.distance_jitter)
        value = int(round(center + (amplitude * wave) + noise))
        return max(self.distance_min, min(self.distance_max, value))

    def _build_voltage_centivolts(self):
        value = self.voltage_base + random.uniform(-self.voltage_jitter, self.voltage_jitter)
        value = max(3.0, min(5.5, value))
        return int(round(value * 100.0))

    def _build_rssi(self):
        return int(self.rssi_base + random.randint(-self.rssi_jitter, self.rssi_jitter))

    def _handle_response_interval(self, response):
        header_wpl = response.headers.get("wpl", "")
        try:
            wpl = int(header_wpl)
            if wpl > 0:
                self.current_interval = wpl
                return
        except Exception:
            pass
        self.current_interval = self.default_interval

    def send_update(self):
        distance_cm = self._build_distance_cm()
        voltage_cv = self._build_voltage_centivolts()
        rssi = self._build_rssi()

        params = {
            "key": self.private_key,
            "distance": str(distance_cm),
            "voltage": str(voltage_cv),
        }

        headers = {
            "FW-Version": str(self.fw_version),
            "RSSI": str(rssi),
        }
        if self.host_header:
            headers["Host"] = self.host_header

        response = requests.get(
            self.update_url,
            params=params,
            headers=headers,
            timeout=self.timeout,
            verify=self.verify_tls,
        )

        body = (response.text or "").strip()
        fw_header = response.headers.get("fw-version", "-")
        wpl_header = response.headers.get("wpl", "-")

        print(
            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"status={response.status_code} body={body} "
            f"pub={self.public_key} "
            f"distance={distance_cm}cm voltage={voltage_cv}cV "
            f"rssi={rssi}dBm resp_fw={fw_header} resp_wpl={wpl_header}"
        )

        if response.status_code == 200 and body == "OK":
            self._handle_response_interval(response)
        else:
            self.current_interval = self.default_interval

    def run(self, once=False):
        while self.running:
            try:
                self.send_update()
            except requests.RequestException as ex:
                self.current_interval = self.default_interval
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] request_error={ex}", file=sys.stderr)
            except Exception as ex:
                self.current_interval = self.default_interval
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] error={ex}", file=sys.stderr)

            if once:
                return

            sleep_s = max(1, int(self.current_interval))
            time.sleep(sleep_s)


def parse_args():
    env_api_domain = os.getenv("API_DOMAIN", "https://api.localhost")
    env_demo_pub = os.getenv("DEMO_S1_PUB_KEY", "1pubDEMO_SENSOR_S1")
    env_demo_prv = os.getenv("DEMO_S1_PRV_KEY", "1prvDEMO_SENSOR_S1")

    parser = argparse.ArgumentParser(
        description="Simulate a WiFi Water Level S1 device posting updates to WLP API /update"
    )
    parser.add_argument("--base-url", default=env_api_domain, help="API base URL, example: https://api.localhost")
    parser.add_argument("--public-key", default=env_demo_pub, help="Device public key from .env (used for logs)")
    parser.add_argument("--private-key", default=env_demo_prv, help="Device private key from .env")
    parser.add_argument("--fw-version", type=int, default=22, help="Firmware version sent in FW-Version header")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds")

    parser.add_argument("--verify-tls", action="store_true", help="Enable TLS certificate verification")
    parser.add_argument("--host-header", default="", help="Optional Host header override (useful with --base-url https://localhost)")

    parser.add_argument("--interval", type=int, default=30, help="Default posting interval in seconds")

    parser.add_argument("--distance-min", type=int, default=18, help="Minimum simulated distance in cm")
    parser.add_argument("--distance-max", type=int, default=145, help="Maximum simulated distance in cm")
    parser.add_argument("--distance-jitter", type=int, default=2, help="Random distance jitter in cm")
    parser.add_argument("--wave-period", type=int, default=300, help="Wave period in seconds used for smooth level changes")

    parser.add_argument("--voltage-base", type=float, default=4.10, help="Base battery voltage in volts")
    parser.add_argument("--voltage-jitter", type=float, default=0.05, help="Random voltage jitter in volts")

    parser.add_argument("--rssi-base", type=int, default=-61, help="Base RSSI in dBm")
    parser.add_argument("--rssi-jitter", type=int, default=4, help="Random RSSI jitter in dBm")

    parser.add_argument("--once", action="store_true", help="Send only one update and exit")

    args = parser.parse_args()
    if args.distance_min > args.distance_max:
        parser.error("--distance-min must be <= --distance-max")
    return args


def main():
    args = parse_args()
    if not args.verify_tls:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    service = S1DemoDeviceService(args)

    def _stop(*_):
        service.running = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    service.run(once=args.once)


if __name__ == "__main__":
    main()
