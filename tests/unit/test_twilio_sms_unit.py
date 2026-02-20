import unittest
from unittest.mock import MagicMock, patch

import twilio_sms


class TwilioSmsUnitTestCase(unittest.TestCase):
    def test_send_phone_verify_code_uses_client(self):
        fake_client = MagicMock()
        with patch("twilio_sms.Client", return_value=fake_client):
            twilio_sms.send_phone_verify_code("+15550001111", 123456)
            fake_client.messages.create.assert_called_once()

    def test_send_alert_returns_false_on_low_balance(self):
        with patch("twilio_sms.db.User.get_sms_credits", return_value=0.0):
            self.assertFalse(twilio_sms.send_alert(1, "+15550001111", "Alert"))

    def test_send_alert_consumes_credits_and_sends(self):
        fake_client = MagicMock()
        with patch("twilio_sms.db.User.get_sms_credits", return_value=1.0), \
            patch("twilio_sms.db.User.consume_sms_credits") as consume, \
            patch("twilio_sms.Client", return_value=fake_client):
            result = twilio_sms.send_alert(1, "+15550001111", "Alert message")
            self.assertIsNone(result)
            consume.assert_called_once()
            fake_client.messages.create.assert_called_once()


if __name__ == "__main__":
    unittest.main()
