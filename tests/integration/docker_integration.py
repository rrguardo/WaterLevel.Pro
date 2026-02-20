import subprocess
import time
from pathlib import Path

import requests


ROOT_DIR = Path(__file__).resolve().parents[2]
COMPOSE_FILE = ROOT_DIR / "docker" / "docker-compose.yml"
ENV_FILE = ROOT_DIR / ".env"
ENV_EXAMPLE_FILE = ROOT_DIR / ".env.example"


_STACK_READY = False


def _read_env_file(path):
    values = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        values[key.strip()] = value
    return values


def load_runtime_settings():
    if not ENV_FILE.exists():
        ENV_FILE.write_text(ENV_EXAMPLE_FILE.read_text(encoding="utf-8"), encoding="utf-8")

    env_values = _read_env_file(ENV_FILE)
    web_host = env_values.get("WLP_SERVER_NAME", "localhost")
    api_host = env_values.get("WLP_API_SERVER_NAME", "api.localhost")

    return {
        "web_host": web_host,
        "api_host": api_host,
        "base_url": "https://localhost",
        "app_domain": env_values.get("APP_DOMAIN", "https://localhost"),
        "demo_s1_pub_key": env_values.get("DEMO_S1_PUB_KEY", "1pubDEMO_SENSOR_S1"),
        "demo_s1_prv_key": env_values.get("DEMO_S1_PRV_KEY", "1prvDEMO_SENSOR_S1"),
        "demo_relay_pub_key": env_values.get("DEMO_RELAY_PUB_KEY", "3pubDEMO_RELAY_R1"),
        "demo_relay_prv_key": env_values.get("DEMO_RELAY_PRV_KEY", "3prvDEMO_RELAY_R1"),
    }


def _run_compose(*args):
    command = ["docker", "compose", "-f", str(COMPOSE_FILE), *args]
    return subprocess.run(command, cwd=ROOT_DIR, check=True, capture_output=True, text=True)


def start_stack(timeout_seconds=180):
    global _STACK_READY
    if _STACK_READY:
        return

    runtime = load_runtime_settings()

    _run_compose("down", "-v")
    _run_compose("up", "--build", "-d", "app", "nginx", "cron", "goaccess")

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            response = requests.get(
                f"{runtime['base_url']}/ping",
                headers={"Host": runtime["web_host"]},
                timeout=2,
                verify=False,
            )
            if response.status_code == 200 and "PONG" in response.text:
                _STACK_READY = True
                return
        except requests.RequestException:
            pass
        time.sleep(2)

    raise RuntimeError("Docker stack did not become ready in time")


def stop_stack():
    global _STACK_READY
    if not _STACK_READY:
        return

    _run_compose("down", "-v")
    _STACK_READY = False
