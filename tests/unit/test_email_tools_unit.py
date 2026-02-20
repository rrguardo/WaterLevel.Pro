import unittest
from unittest.mock import MagicMock, patch

import email_tools


class EmailToolsUnitTestCase(unittest.TestCase):
    def test_generate_and_check_confirmation_code(self):
        code = email_tools.generate_confirmation_code("u@example.com")
        self.assertTrue(email_tools.check_confirmation_code("u@example.com", code))
        self.assertFalse(email_tools.check_confirmation_code("u@example.com", "bad-code"))

    def test_send_register_email_calls_deliver(self):
        with patch("email_tools._deliver_message") as deliver:
            email_tools.send_register_email("u@example.com", lang="en")
            deliver.assert_called_once()

    def test_send_alert_email_calls_deliver(self):
        with patch("email_tools._deliver_message") as deliver:
            email_tools.send_alert_email("u@example.com", "Alert", "Body")
            deliver.assert_called_once()

    def test_support_email_calls_deliver(self):
        with patch("email_tools._deliver_message") as deliver:
            email_tools.support_email("u@example.com", "Support body")
            deliver.assert_called_once()

    def test_deliver_message_auth_mismatch_raises(self):
        message = MagicMock()
        with patch("email_tools.SMTP_TEST", False), \
            patch("email_tools.SMTP_USERNAME", "user"), \
            patch("email_tools.SMTP_PASSWORD", ""):
            with self.assertRaises(ValueError):
                email_tools._deliver_message(message)


if __name__ == "__main__":
    unittest.main()
