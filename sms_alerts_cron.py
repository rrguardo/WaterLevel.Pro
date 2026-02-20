from flask import Flask
from flask_caching import Cache

import settings
import twilio_sms

import redis
import time
import logging


def setup_logger():
    # Configure the logging system
    """Configure logging output for the SMS alerts cron runner.

    Returns:
        None.
    """
    logging.basicConfig(level=logging.WARNING, handlers=[])  # Do not add the implicit handler
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Create a handler and set the formatter
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # Add the handler to the root logger
    logging.getLogger().addHandler(handler)


setup_logger()
import db

app = Flask(__name__)
app.config['SECRET_KEY'] = settings.APP_SEC_KEY

app.config.update(settings.API_CACHE_SETT)
cache = Cache(app)
db.cache.init_app(app)

redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.API_REDIS_DB,
    decode_responses=True
)


if __name__ == "__main__":

    phone_alerts_data = db.CronsDB.get_sms_alerts_info()
    local_cache = {}
    logging.warning(f"Total alerts to check: {len(phone_alerts_data)}")
    for data in phone_alerts_data:
        try:
            device_id = data.device_id
            condition = int(data.condition)
            level = int(data.level)
            phone = data.phone
            user_id = data.user_id
            frequency = int(data.frequency)
            logging.warning(f"Working on {phone} --- condition:{condition} --- level: {level}")

            freq_check = redis_client.get(f"alert-frequency/{condition}/{phone}")
            if freq_check:
                freq_check = int(freq_check)
                diff_time = int(time.time()) - int(freq_check)
                diff_time = diff_time/(60*60)
                if diff_time < frequency:
                    logging.warning(f"skip by freq: {phone}")
                    continue

            # =============================================================
            #     Section to load Device Info (level %, online-time)
            if not local_cache.get(device_id):
                s1_info = db.DevicesDB.load_s1_info(device_id)
                sensor_key = s1_info.public_key

                cache_key = f'tin-keys/{sensor_key}'
                sensor_data = redis_client.get(cache_key)

                distance = 0
                rtime = 0
                percent = 0
                rtime = 0

                local_cache[device_id] = [s1_info.WIFI_POOL_TIME, rtime, percent, sensor_key]

                if sensor_data:
                    distance, rtime, voltage, rssi = sensor_data.split("|")

                if s1_info.WIFI_POOL_TIME:

                    EMPTY_LEVEL = s1_info.EMPTY_LEVEL
                    TOP_MARGIN = s1_info.TOP_MARGIN
                    WIFI_POOL_TIME = s1_info.WIFI_POOL_TIME

                    distance = int(distance)
                    if EMPTY_LEVEL == 0:
                        EMPTY_LEVEL = 1
                    percent = min(100, 100 - min(100, int(((distance - TOP_MARGIN) * 100.0) / ((EMPTY_LEVEL - TOP_MARGIN)))))
                    local_cache[device_id] = [s1_info.WIFI_POOL_TIME, rtime, percent, sensor_key]
                else:
                    logging.warning("Missing sensor settings!")
                    continue

            # =====================================================
            if local_cache.get(device_id) and len(local_cache.get(device_id)) == 4 and not local_cache.get(phone):
                WIFI_POOL_TIME, rtime, percent, sensor_key = local_cache.get(device_id)

                public_name = db.DevicesDB.get_user_device_name(data.user_id, sensor_key)
                if not public_name:
                    public_name = sensor_key

                if condition == 2:
                    diff_time = int(time.time()) - int(rtime)
                    if (diff_time > WIFI_POOL_TIME*3 + 20) or rtime == 0:
                        # offline condition detected
                        local_cache[phone] = True
                        redis_client.set(f"alert-frequency/{condition}/{phone}", int(time.time()))
                        alert_msg = f"Offline Alert: {public_name[:15]} disconnected. "
                        twilio_sms.send_alert(user_id, phone, alert_msg)
                        logging.warning(f"{alert_msg}--- email: {phone}")
                if condition == 1 and percent >= level:
                    # send alert
                    redis_client.set(f"alert-frequency/{condition}/{phone}", int(time.time()))
                    alert_msg = f"Alert: {public_name[:15]} Level Is Above {level}%. "
                    twilio_sms.send_alert(user_id, phone, alert_msg)
                    logging.warning(f"{alert_msg}--- email: {phone}")
                if condition == -1 and percent <= level:
                    # send alert
                    redis_client.set(f"alert-frequency/{condition}/{phone}", int(time.time()))
                    alert_msg = f"Alert: {public_name[:15]} Level Is Below {level}%. "
                    twilio_sms.send_alert(user_id, phone, alert_msg)
                    logging.warning(f"{alert_msg}--- email: {phone}")
        except Exception as ex:
            logging.exception(ex)
