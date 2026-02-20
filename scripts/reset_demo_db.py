import argparse
import hashlib
import shutil
import sqlite3
from pathlib import Path


ADMIN_EMAIL = "admin.demo@opensource.local"
ADMIN_PASSWORD = "AdminDemo_2026_Open!"
ADMIN_PHONE = 1000000000

DEMO_DEVICES = [
    (1, 1, "1pubDEMO_SENSOR_S1", "1prvDEMO_SENSOR_S1", "Open-source demo device type 1"),
    (2, 2, "2pubDEMO_SENSOR_S2", "2prvDEMO_SENSOR_S2", "Open-source demo device type 2"),
    (3, 3, "3pubDEMO_RELAY_R1", "3prvDEMO_RELAY_R1", "Open-source demo device type 3"),
]


def rebuild_demo_dataset(db_path: Path) -> None:
    """Reset and repopulate a SQLite database with open-source demo records.

    Args:
        db_path: Filesystem path to target SQLite database.

    Returns:
        None.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=OFF")

    admin_hash = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()

    for table in [
        "user_alerts",
        "user_devices",
        "user_settings",
        "user_sms_credits",
        "users",
        "pp_ipn",
        "support_info",
        "device_subscriptions",
        "device_uptime",
        "relay_events",
        "unlocked_devices",
        "sensor_settings",
        "relay_settings",
        "devices",
    ]:
        cur.execute(f"DELETE FROM {table}")

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
    if cur.fetchone():
        for table in ["users", "devices", "user_devices", "support_info", "relay_events"]:
            cur.execute("DELETE FROM sqlite_sequence WHERE name=?", (table,))

    cur.execute(
        """
        INSERT INTO users (id, email, passw, is_admin, confirmed, phone)
        VALUES (?, ?, ?, 1, 1, ?)
        """,
        (1, ADMIN_EMAIL, admin_hash, ADMIN_PHONE),
    )

    cur.executemany(
        """
        INSERT INTO devices (id, type, public_key, private_key, note)
        VALUES (?, ?, ?, ?, ?)
        """,
        DEMO_DEVICES,
    )

    cur.executemany(
        """
        INSERT INTO sensor_settings (device, EMPTY_LEVEL, TOP_MARGIN, WIFI_POOL_TIME, SONIC_POOL_TIME, CurrentStatus)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (1, 150, 25, 30, 3, 1),
            (2, 200, 25, 30, 3, 1),
        ],
    )

    cur.execute(
        """
        INSERT INTO relay_settings (device, ALGO, START_LEVEL, END_LEVEL, AUTO_OFF, AUTO_ON, MIN_FLOW_MM_X_MIN,
                                    SENSOR_KEY, BLIND_DISTANCE, HOURS_OFF, SAFE_MODE)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (3, 0, 30, 95, 1, 1, 10, "1pubDEMO_SENSOR_S1", 22, "", 1),
    )

    cur.executemany(
        """
        INSERT INTO user_devices (user_id, device_id, name, can_admin)
        VALUES (?, ?, ?, ?)
        """,
        [
            (1, 1, "Demo Sensor S1", 1),
            (1, 2, "Demo Sensor S2", 1),
            (1, 3, "Demo Relay R1", 1),
        ],
    )

    cur.executemany(
        """
        INSERT INTO user_settings (user_id, setting_name, setting_value)
        VALUES (?, ?, ?)
        """,
        [
            (1, "email-alert", "off"),
            (1, "sms-alert", "off"),
            (1, "frequency-alert", "6"),
        ],
    )

    conn.commit()
    conn.close()


def main() -> None:
    """Parse CLI arguments and rebuild target/source demo databases.

    Returns:
        None.
    """
    parser = argparse.ArgumentParser(description="Reset demo SQLite dataset for open-source usage")
    parser.add_argument("--target", default="database.db", help="Target database file used by app")
    parser.add_argument(
        "--source",
        default="database.opensource.db",
        help="Source schema database file to copy before applying demo dataset",
    )
    parser.add_argument(
        "--sync-source",
        action="store_true",
        help="Also apply the same demo dataset to source file",
    )
    args = parser.parse_args()

    source = Path(args.source)
    target = Path(args.target)

    if not source.exists():
        raise FileNotFoundError(f"Source database not found: {source}")

    shutil.copyfile(source, target)
    rebuild_demo_dataset(target)

    if args.sync_source:
        rebuild_demo_dataset(source)

    print("Demo DB reset completed")
    print(f"Target: {target}")
    print(f"Source synced: {args.sync_source}")
    print(f"Admin email: {ADMIN_EMAIL}")
    print(f"Admin password: {ADMIN_PASSWORD}")


if __name__ == "__main__":
    main()
