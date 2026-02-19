import argparse
import os
import random
import signal
import sys
import time

import requests
import urllib3


class R1DemoRelayService:
    def __init__(self, args):
        self.base_url = args.base_url.rstrip("/")
        self.update_url = f"{self.base_url}/relay-update"

        self.public_key = args.public_key
        self.private_key = args.private_key
        self.fw_version = args.fw_version
        self.timeout = args.timeout
        self.verify_tls = args.verify_tls
        self.host_header = args.host_header

        self.default_interval = max(1, args.interval)
        self.current_interval = self.default_interval

        self.rssi_base = args.rssi_base
        self.rssi_jitter = max(0, args.rssi_jitter)

        self.events = args.events
        self.random_events = args.random_events
        self.running = True
        self.relay_status = max(0, min(1, args.status))

    def _build_rssi(self):
        return int(self.rssi_base + random.randint(-self.rssi_jitter, self.rssi_jitter))

    def _build_events_header(self):
        if not self.random_events:
            return self.events

        base = [0, 0, 0, 0, 0]
        chance = random.random()
        if chance < 0.06:
            base[0] = random.choice([3, 4, 5, 6, 7, 10, 11, 12])
        return ",".join(str(item) for item in base)

    def _handle_response_interval(self, response):
        header_pool = response.headers.get("pool-time", "")
        try:
            pool_time = int(header_pool)
            if pool_time > 0:
                self.current_interval = pool_time
                return
        except Exception:
            pass
        self.current_interval = self.default_interval

    def send_update(self):
        rssi = self._build_rssi()
        events = self._build_events_header()

        params = {
            "key": self.private_key,
            "status": str(self.relay_status),
        }

        headers = {
            "FW-Version": str(self.fw_version),
            "RSSI": str(rssi),
            "EVENTS": events,
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
        resp_fw = response.headers.get("fw-version", "-")
        resp_pool = response.headers.get("pool-time", "-")
        resp_action = response.headers.get("ACTION", "-")
        resp_percent = response.headers.get("percent", "-")

        print(
            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"status={response.status_code} body={body} "
            f"pub={self.public_key} relay_status={self.relay_status} "
            f"events={events} rssi={rssi}dBm "
            f"resp_fw={resp_fw} resp_pool={resp_pool} resp_action={resp_action} resp_percent={resp_percent}"
        )

        if response.status_code == 200 and body == "OK":
            self._handle_response_interval(response)
            try:
                action = int(resp_action)
                if action == 1:
                    self.relay_status = 1
                elif action == -1:
                    self.relay_status = 0
            except Exception:
                pass
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
    env_demo_pub = os.getenv("DEMO_RELAY_PUB_KEY", "3pubDEMO_RELAY_R1")
    env_demo_prv = os.getenv("DEMO_RELAY_PRV_KEY", "3prvDEMO_RELAY_R1")

    parser = argparse.ArgumentParser(
        description="Simulate a WiFi Smart Water Pump Controller S1 relay posting to WLP API /relay-update"
    )
    parser.add_argument("--base-url", default=env_api_domain, help="API base URL, example: https://api.localhost")
    parser.add_argument("--public-key", default=env_demo_pub, help="Relay public key from .env (used for logs)")
    parser.add_argument("--private-key", default=env_demo_prv, help="Relay private key from .env")
    parser.add_argument("--fw-version", type=int, default=19, help="Firmware version sent in FW-Version header")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds")

    parser.add_argument("--verify-tls", action="store_true", help="Enable TLS certificate verification")
    parser.add_argument("--host-header", default="", help="Optional Host header override (useful with --base-url https://localhost)")

    parser.add_argument("--interval", type=int, default=30, help="Default posting interval in seconds")
    parser.add_argument("--status", type=int, default=0, choices=[0, 1], help="Relay status sent to API (0=off, 1=on)")

    parser.add_argument("--events", default="0,0,0,0,0", help="EVENTS header payload as 5 comma-separated integers")
    parser.add_argument("--random-events", action="store_true", help="Inject occasional random demo events")

    parser.add_argument("--rssi-base", type=int, default=-59, help="Base RSSI in dBm")
    parser.add_argument("--rssi-jitter", type=int, default=5, help="Random RSSI jitter in dBm")

    parser.add_argument("--once", action="store_true", help="Send only one update and exit")

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    if not args.verify_tls:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    service = R1DemoRelayService(args)

    def _stop(*_):
        service.running = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    service.run(once=args.once)


if __name__ == "__main__":
    main()
