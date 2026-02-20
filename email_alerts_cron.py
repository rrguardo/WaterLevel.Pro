from flask import Flask
from flask_caching import Cache

import settings
import email_tools

import redis
import time
import logging


def setup_logger():
    # Configure the logging system
    """Configure logging output for the email alerts cron runner.

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

    email_alerts_data = db.CronsDB.get_email_alerts_info()
    local_cache = {}
    logging.warning(f"Total alerts to check: {len(email_alerts_data)}")
    for data in email_alerts_data:
        try:
            device_id = data.device_id
            condition = int(data.condition)
            level = int(data.level)
            email = data.email
            frequency = int(data.frequency)
            logging.debug(f"Working on {email} --- condition:{condition} --- level: {level}")

            freq_check = redis_client.get(f"alert-frequency/{condition}/{email}")
            if freq_check:
                freq_check = int(freq_check)
                diff_time = int(time.time()) - int(freq_check)
                diff_time = diff_time/(60*60)
                if diff_time < frequency:
                    logging.debug(f"skip by freq: {email}")
                    continue

            # =============================================================
            #     Section to load Device Info (level %, online-time)
            if not local_cache.get(device_id):
                s1_info = db.DevicesDB.load_s1_info(device_id)
                if not s1_info:
                    logging.error(f"Invalid S1 device_id: {device_id}")
                    continue
                sensor_key = s1_info.public_key

                cache_key = f'tin-keys/{sensor_key}'
                sensor_data = redis_client.get(cache_key)

                distance = 0
                rtime = 0
                percent = 0

                local_cache[device_id] = [s1_info.WIFI_POOL_TIME, rtime, percent, sensor_key]
                if sensor_data and s1_info.WIFI_POOL_TIME:
                    distance, rtime, voltage, rssi = sensor_data.split("|")

                    EMPTY_LEVEL = s1_info.EMPTY_LEVEL
                    TOP_MARGIN = s1_info.TOP_MARGIN
                    WIFI_POOL_TIME = s1_info.WIFI_POOL_TIME

                    distance = int(distance)
                    if EMPTY_LEVEL == 0:
                        EMPTY_LEVEL = 1
                    percent = min(100, 100 - min(100, int(((distance - TOP_MARGIN) * 100.0) / ((EMPTY_LEVEL - TOP_MARGIN)))))
                    local_cache[device_id] = [s1_info.WIFI_POOL_TIME, rtime, percent, sensor_key]
                else:
                    logging.debug("Missing sensor data!")
                    continue

            # =====================================================
            if local_cache.get(device_id) and len(local_cache.get(device_id)) == 4 and not local_cache.get(email):
                WIFI_POOL_TIME, rtime, percent, sensor_key = local_cache.get(device_id)

                public_name = db.DevicesDB.get_user_device_name(data.user_id, sensor_key)
                if not public_name:
                    public_name = sensor_key

                if condition == 2:
                    diff_time = int(time.time()) - int(rtime)
                    if diff_time > WIFI_POOL_TIME*3 + 20:
                        # offline condition detected
                        local_cache[email] = True
                        redis_client.set(f"alert-frequency/{condition}/{email}", int(time.time()))
                        alert_subject = f"Offline Alert: {public_name[:15]} is offline [WaterLevel.Pro]"
                        alert_body = f""" <h2>Offline Alert!</h2>
                        <p>Device {public_name} is <b>offline</b>. <br>
                        Check internet connection, WiFi coverage and power sources.</p>
                        """
                        email_tools.send_alert_email(email, alert_subject, alert_body)
                        logging.warning(f"{alert_subject}--- email: {email}")
                if condition == 1 and percent >= level:
                    # send alert
                    redis_client.set(f"alert-frequency/{condition}/{email}", int(time.time()))
                    alert_subject = f"Alert: {public_name[:15]} Level Is Above {level}% [WaterLevel.Pro]"
                    alert_body = f""" <h2>Level Above {level}% Alert!</h2>
                                        <p>Device {public_name} level is <b>{percent}%</b>.</p>
                                        <p>
                                            To reduce false alerts, remember install sensor away the tank water 
                                            inlet and away from interference devices.
                                        </p>
                                        """
                    email_tools.send_alert_email(email, alert_subject, alert_body)
                    logging.warning(f"{alert_subject}--- email: {email}")
                if condition == -1 and percent <= level:
                    # send alert
                    redis_client.set(f"alert-frequency/{condition}/{email}", int(time.time()))
                    alert_subject = f"Alert: {public_name[:15]} Level Is Below {level}% [WaterLevel.Pro]"
                    alert_body = f""" <h2>Level Below {level}% Alert!</h2>
                                <p>Device {public_name} level is <b>{percent}%</b>.</p>
                                <p>
                                    To reduce false alerts, remember install sensor away the tank water 
                                    inlet and away from interference devices.
                                </p>
                                """
                    email_tools.send_alert_email(email, alert_subject, alert_body)
                    logging.warning(f"{alert_subject}--- email: {email}")
        except Exception as ex:
            logging.exception(ex)
