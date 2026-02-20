import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from flask import Flask

import db


class _CtxConn:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        return False


class DbUnitTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._app = Flask(__name__)
        cls._app.config.update({
            "CACHE_TYPE": "SimpleCache",
            "CACHE_DEFAULT_TIMEOUT": 300,
        })
        db.cache.init_app(cls._app)

    def _fake_connection(self, fetchone=None, fetchall=None, execute_result=None):
        fake_result = MagicMock()
        fake_result.fetchone.return_value = fetchone
        fake_result.fetchall.return_value = fetchall if fetchall is not None else []

        fake_conn = MagicMock()
        fake_conn.execute.return_value = execute_result if execute_result is not None else fake_result
        return fake_conn, fake_result

    def test_valid_hours_list(self):
        self.assertTrue(db.valid_hours_list("0,1,2,23"))
        self.assertFalse(db.valid_hours_list("24,1"))
        self.assertFalse(db.valid_hours_list("1,,2"))

    def test_get_user_lookup_helpers(self):
        fake_conn, _ = self._fake_connection(fetchone=SimpleNamespace(id=1, email="u@example.com"))
        with patch.object(db.engine, "connect", return_value=_CtxConn(fake_conn)):
            self.assertEqual(1, db.get_user_by_id.uncached(123).id)
            self.assertEqual("u@example.com", db.get_user_by_email.uncached("u@example.com").email)

    def test_valid_4register_true_when_not_found(self):
        fake_result = MagicMock()
        fake_result.fetchone.return_value = None
        fake_conn = MagicMock()
        fake_conn.execute.return_value = fake_result

        with patch.object(db.engine, "connect", return_value=_CtxConn(fake_conn)):
            self.assertTrue(db.valid_4register("new@example.com"))

    def test_valid_4register_false_when_confirmed(self):
        fake_result = MagicMock()
        fake_result.fetchone.return_value = SimpleNamespace(confirmed=1)
        fake_conn = MagicMock()
        fake_conn.execute.return_value = fake_result

        with patch.object(db.engine, "connect", return_value=_CtxConn(fake_conn)):
            self.assertFalse(db.valid_4register("used@example.com"))

    def test_add_user_and_confirm_user(self):
        fake_conn = MagicMock()
        fake_conn.execute.return_value = object()

        with patch.object(db.engine, "connect", return_value=_CtxConn(fake_conn)):
            self.assertTrue(db.add_user("u@example.com", "hash"))
            self.assertTrue(db.confirm_user("u@example.com"))
            self.assertGreaterEqual(fake_conn.commit.call_count, 2)

    def test_try_login_returns_row(self):
        fake_result = MagicMock()
        fake_result.fetchone.return_value = SimpleNamespace(id=7)
        fake_conn = MagicMock()
        fake_conn.execute.return_value = fake_result

        with patch.object(db.engine, "connect", return_value=fake_conn):
            row = db.try_login("u@example.com", "hash")
            self.assertEqual(7, row.id)

    def test_cronsdb_get_alerts_info(self):
        fake_result = MagicMock()
        fake_result.fetchall.return_value = [SimpleNamespace(device_id=1)]
        fake_conn = MagicMock()
        fake_conn.execute.return_value = fake_result

        with patch.object(db.engine, "connect", return_value=fake_conn):
            email_rows = db.CronsDB.get_email_alerts_info()
            sms_rows = db.CronsDB.get_sms_alerts_info()
            self.assertEqual(1, len(email_rows))
            self.assertEqual(1, len(sms_rows))

    def test_pp_ipn_helpers(self):
        fake_conn, _ = self._fake_connection(fetchone=SimpleNamespace(payment_status="Completed"))
        with patch.object(db.engine, "connect", return_value=fake_conn):
            self.assertEqual("Completed", db.PP_IPN.ipn_status("txn123"))

        fake_conn_ctx, _ = self._fake_connection(execute_result=object())
        with patch.object(db.engine, "connect", return_value=_CtxConn(fake_conn_ctx)):
            self.assertTrue(db.PP_IPN.add_pp_ipn("txn1", "Completed", "r@e.com", "p@e.com", 1.0, "-", 1, "item"))

    def test_devicesdb_simple_loaders(self):
        fake_conn, _ = self._fake_connection(fetchone=SimpleNamespace(up_hours=12))
        with patch.object(db.engine, "connect", return_value=fake_conn):
            self.assertEqual(12, db.DevicesDB.get_device_uptime.uncached(1))

        fake_conn, _ = self._fake_connection(fetchone=SimpleNamespace(public_key="1pubX"))
        with patch.object(db.engine, "connect", return_value=fake_conn):
            self.assertEqual("1pubX", db.DevicesDB.valid_private_key.uncached("1prvX"))

        fake_conn, _ = self._fake_connection(fetchone=SimpleNamespace(id=9))
        with patch.object(db.engine, "connect", return_value=fake_conn):
            self.assertEqual(9, db.DevicesDB.load_device_id_by_public_key.uncached("1pubZ"))

    def test_devicesdb_load_settings_and_info(self):
        fake_conn, _ = self._fake_connection(fetchone=SimpleNamespace(public_key="1pubA", WIFI_POOL_TIME=30))
        with patch.object(db.engine, "connect", return_value=fake_conn):
            self.assertIsNotNone(db.DevicesDB.load_s1_info(2))

        fake_conn, _ = self._fake_connection(fetchone=SimpleNamespace(device=2, ALGO=1))
        with patch.object(db.engine, "connect", return_value=fake_conn):
            self.assertIsNotNone(db.DevicesDB.load_relay_settings.uncached(2))

        with patch("db.DevicesDB.load_relay_settings", return_value=SimpleNamespace(ALGO=1)):
            self.assertEqual(1, db.DevicesDB.load_device_settings(3, 3).ALGO)

    def test_devicesdb_update_methods(self):
        fake_conn, _ = self._fake_connection(execute_result=object())
        with patch.object(db.engine, "connect", return_value=_CtxConn(fake_conn)), patch.object(db.cache, "delete_memoized"):
            self.assertTrue(db.DevicesDB.update_sensor_settings(10, EMPTY_LEVEL=200, TOP_MARGIN=20, WIFI_POOL_TIME=60))
            self.assertTrue(db.DevicesDB.update_sensor_pool_time(10, 90))
            self.assertTrue(db.DevicesDB.update_relay_settings(11, ALGO=1, START_LEVEL=30, END_LEVEL=90))
            self.assertTrue(db.DevicesDB.turn_off_relay_smart_mode(11))

    def test_devicesdb_get_user_metadata_methods(self):
        fake_conn, _ = self._fake_connection(fetchone=SimpleNamespace(name="Tank"))
        with patch.object(db.engine, "connect", return_value=fake_conn):
            self.assertEqual("Tank", db.DevicesDB.get_user_device_name.uncached(1, "1pubA"))

        fake_conn, _ = self._fake_connection(fetchone=SimpleNamespace(can_admin=1))
        with patch.object(db.engine, "connect", return_value=fake_conn):
            self.assertTrue(db.DevicesDB.user_can_admin_device.uncached(1, "1pubA"))

    def test_devicesdb_get_all_devices_and_events(self):
        rows = [SimpleNamespace(id=1, public_key="1pub", private_key="1prv", note=None)]
        fake_conn, _ = self._fake_connection(fetchall=rows)
        with patch.object(db.engine, "connect", return_value=fake_conn):
            devices = db.DevicesDB.get_all_devices_by_type(1)
            self.assertEqual(1, len(devices))

        event_rows = [SimpleNamespace(id=1, events="1,2", created_at="2026-01-01")]
        fake_conn, _ = self._fake_connection(fetchall=event_rows)
        with patch.object(db.engine, "connect", return_value=fake_conn):
            events = db.DevicesDB.get_relay_events.uncached(1, 20)
            self.assertEqual("1,2", events[0]["events"])

    def test_devicesdb_add_device_paths(self):
        exec_result = SimpleNamespace(lastrowid=42)
        fake_conn, _ = self._fake_connection(execute_result=exec_result)
        with patch.object(db.engine, "connect", return_value=_CtxConn(fake_conn)), \
            patch("db.DevicesDB.update_sensor_settings") as update_sensor, \
            patch("db.DevicesDB.update_relay_settings") as update_relay:
            self.assertTrue(db.DevicesDB.add_device("1prv", "1pub", "note", 1))
            self.assertTrue(db.DevicesDB.add_device("3prv", "3pub", "note", 3))
            update_sensor.assert_called_once_with(42)
            update_relay.assert_called_once_with(42)

    def test_user_model_methods(self):
        user = db.User(1, "u@example.com", "hash", 0)

        device_row = SimpleNamespace(id=7)
        fake_conn, _ = self._fake_connection(execute_result=object())
        with patch("db.DevicesDB.load_device_by_public_key", return_value=device_row), \
            patch.object(db.engine, "connect", return_value=_CtxConn(fake_conn)), \
            patch.object(db.cache, "delete_memoized"):
            self.assertTrue(user.add_device("1pub", name="tank", can_admin=1))
            self.assertTrue(user.add_alert("1pub", 1, 50))
            self.assertTrue(user.delete_alert("1pub", 1, 50))

        with patch.object(db.engine, "connect", return_value=_CtxConn(fake_conn)), patch.object(db.cache, "delete_memoized"):
            self.assertTrue(user.remove_device("1pub"))
            self.assertTrue(user.set_phone(573000000000))
            self.assertTrue(user.set_setting("email-alert", "on"))

    def test_user_static_queries(self):
        fake_conn, _ = self._fake_connection(fetchall=[SimpleNamespace(condition=1, level=50)])
        with patch("db.DevicesDB.load_device_by_public_key", return_value=SimpleNamespace(id=9)), patch.object(db.engine, "connect", return_value=fake_conn):
            self.assertEqual(1, len(db.User.load_device_alerts.uncached(1, "1pub")))

        fake_conn, _ = self._fake_connection(fetchall=[SimpleNamespace(public_key="1pub", name="n", can_admin=1, type=1, long_name="S1")])
        with patch.object(db.engine, "connect", return_value=fake_conn):
            self.assertEqual(1, len(db.User.load_user_devices.uncached(1)))

        fake_conn, _ = self._fake_connection(fetchall=[SimpleNamespace(setting_name="email-alert", setting_value="on")])
        with patch.object(db.engine, "connect", return_value=fake_conn):
            settings_dict = db.User.get_user_settings.uncached(1)
            self.assertEqual("on", settings_dict["email-alert"])

        fake_conn, _ = self._fake_connection(fetchone=SimpleNamespace(credits=2.5))
        with patch.object(db.engine, "connect", return_value=fake_conn):
            self.assertEqual(2.5, db.User.get_sms_credits.uncached(1))

    def test_user_credit_and_list_helpers(self):
        fake_conn, _ = self._fake_connection(execute_result=object())
        with patch("db.User.get_sms_credits", return_value=1.0), patch.object(db.engine, "connect", return_value=_CtxConn(fake_conn)), patch.object(db.cache, "delete_memoized"):
            self.assertTrue(db.User.add_sms_credits(1, 0.5))
            self.assertTrue(db.User.consume_sms_credits(1, 0.2))

        users_rows = [SimpleNamespace(id=1, email="u@example.com", phone=None, confirmed=1)]
        fake_conn, _ = self._fake_connection(fetchall=users_rows)
        with patch.object(db.engine, "connect", return_value=fake_conn):
            users = db.User.get_all_users()
            self.assertEqual("yes", users[0]["confirmed"])

    def test_support_helpers(self):
        support_rows = [SimpleNamespace(id=1, user_email="u@example.com", message="m", created_at="now", support_type=0)]
        fake_conn, _ = self._fake_connection(fetchall=support_rows)
        with patch.object(db.engine, "connect", return_value=fake_conn):
            all_support = db.Support.get_all_users_support()
            self.assertEqual("Customer", all_support[0]["support_type"])

        fake_conn, _ = self._fake_connection(fetchall=[SimpleNamespace(id=1, message="m", created_at="now", support_type=0)])
        with patch.object(db.engine, "connect", return_value=fake_conn):
            rows = db.Support.get_user_support.uncached("u@example.com")
            self.assertEqual(1, len(rows))

        fake_conn, _ = self._fake_connection(execute_result=object())
        with patch.object(db.engine, "connect", return_value=_CtxConn(fake_conn)), patch.object(db.cache, "delete_memoized"):
            self.assertTrue(db.Support.add_user_support_record("u@example.com", "hello", support_type=1))


if __name__ == "__main__":
    unittest.main()
