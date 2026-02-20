import subprocess
import unittest

from tests.integration.docker_integration import COMPOSE_FILE, ROOT_DIR, start_stack, stop_stack


class CronIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        start_stack()

    @classmethod
    def tearDownClass(cls):
        stop_stack()

    def _compose_exec_app(self, command):
        full_command = [
            "docker",
            "compose",
            "-f",
            str(COMPOSE_FILE),
            "exec",
            "-T",
            "app",
            "sh",
            "-lc",
            command,
        ]
        result = subprocess.run(full_command, cwd=ROOT_DIR, capture_output=True, text=True)
        return result

    def test_email_alerts_cron_runs(self):
        result = self._compose_exec_app("python /app/email_alerts_cron.py")
        self.assertEqual(0, result.returncode, msg=result.stderr or result.stdout)

    def test_sms_alerts_cron_runs(self):
        result = self._compose_exec_app("python /app/sms_alerts_cron.py")
        self.assertEqual(0, result.returncode, msg=result.stderr or result.stdout)


if __name__ == "__main__":
    unittest.main()
