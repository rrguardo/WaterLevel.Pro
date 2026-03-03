import time
import json
import unittest
from app import app, redis_client
import settings


class SensorStatsUnitTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.pub = 'unittest_pubkey'
        self.history_key = f'tin-history/{self.pub}'
        # flush any existing test key
        try:
            redis_client.delete(self.history_key)
        except Exception:
            pass

    def tearDown(self):
        try:
            redis_client.delete(self.history_key)
        except Exception:
            pass

    def test_sensor_stats_empty(self):
        # No data -> all buckets offline
        rv = self.app.get('/sensor_stats', query_string={'public_key': self.pub})
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertIn('buckets', data)
        self.assertEqual(len(data['buckets']), 24)
        # all buckets should be offline when no samples
        for b in data['buckets']:
            self.assertTrue(b.get('offline', False))

    def test_sensor_stats_with_samples_and_hour_endpoint(self):
        now = int(time.time())
        # create samples for the current hour
        hour_start = now - (now % 3600)
        samples = [
            (hour_start + 10, 50, 3.7),
            (hour_start + 120, 60, 3.75),
            (hour_start + 300, 55, 3.72),
        ]

        # push into redis sorted set as "percent|voltage" with score = ts
        for ts, p, v in samples:
            member = f"{p}|{v}"
            redis_client.zadd(self.history_key, {member: ts})

        # query /sensor_stats and find the bucket with hour_start
        rv = self.app.get('/sensor_stats', query_string={'public_key': self.pub})
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertIn('buckets', data)
        found = False
        for b in data['buckets']:
            if b['hour_start'] == hour_start:
                found = True
                self.assertFalse(b.get('offline', True))
                # percent should be integer rounded average of 50,60,55 -> 55
                self.assertEqual(b['percent'], 55)
                # voltage average approx
                self.assertAlmostEqual(b['voltage'], round((3.7+3.75+3.72)/3, 2))
        self.assertTrue(found)

        # test hour detail endpoint
        rv2 = self.app.get('/sensor_stats_hour', query_string={'public_key': self.pub, 'hour_start': hour_start})
        self.assertEqual(rv2.status_code, 200)
        d2 = json.loads(rv2.data)
        self.assertIn('samples', d2)
        self.assertEqual(len(d2['samples']), 3)
        # samples should be sorted by ts
        ts_list = [s['ts'] for s in d2['samples']]
        self.assertEqual(ts_list, sorted(ts_list))


if __name__ == '__main__':
    unittest.main()
