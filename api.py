import hmac
import hashlib
import secrets
import string
from urllib.parse import unquote

from flask import Flask, render_template, url_for, abort, request, redirect, jsonify, flash
import redis
import time
import logging
from datetime import datetime, timezone, timedelta

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_caching import Cache
from flask_cors import CORS

import requests


import settings
import email_tools


LAST_RELAY_FW_VERSION = 19
LAST_SENSOR_FW_VERSION = 22
DEVELOPER_MODE = True

RELAY_EVENTS_CODE = {
    0: ("NO_EVENT", "No event reported"),
    1: ("BLIND_AREA", "Sensor reach near the blind area!"),
    2: ("BLIND_AREA_DANGER", "Sensor reach near the danger blind area!"),
    3: ("NOT_FLOW", "No water inflow detected!"),
    4: ("OFFLINE", "Offline long time detected!"),
    5: ("IDDLE_SENSOR", "Offline sensor detected!"),
    6: ("END_LEVEL_EVENT", "Reach End Level percent!"),
    7: ("START_LEVEL_EVENT", "Reach Start Level percent!"),
    8: ("SETUP_WIFI", "Wifi setup started"),
    9: ("BOOT", "Device boot!"),
    10: ("PUMP_ON", "Pump ON"),
    11: ("PUMP_OFF", "Pump OFF"),
    12: ("DATA_POST_FAIL", "Fail to post data check internet connection"),
    13: ("BTN_PRESS", "WiFi Reset button pressed"),
    14: ("SENSOR_FAULT", "Sensor fault or cable disconnected!")
}


def setup_logger():
    # Configure the logging system
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


DOMAIN = settings.API_DOMAIN
WEB_APP_DOMAIN = settings.APP_DOMAIN

# Configure CORS for a specific domain
CORS(app, origins=[WEB_APP_DOMAIN])


def generate_secure_random_string(length=16):
    alphabet = string.ascii_letters + string.digits
    password = ''
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3):
            break
    return password


@app.route('/link', methods=["GET"])
def link():
    private_key = request.args.get('key')
    email = request.args.get('email')
    dtype = int(request.args.get('dtype', 1))

    response = app.response_class(
        response='FAIL',
        status=200,
        mimetype='text/plain'
    )
    response.headers['fw-version'] = f"{LAST_SENSOR_FW_VERSION}"
    response.headers['wpl-key'] = f"-"

    if email:
        email = unquote(email)
        if not db.valid_4register(email):
            user_data = db.get_user_by_email(email)

            if user_data:
                current_user1 = db.User(user_data.id, user_data.email, user_data.passw, user_data.is_admin)
                public_key = db.DevicesDB.valid_private_key(private_key) if private_key != "-" else None
                if not public_key:
                    private_key = generate_secure_random_string(22)
                    public_key = generate_secure_random_string(22)
                    note = request.form.get("note", f'added by user: {current_user1.id}')
                    device_id = dtype
                    private_key_format = f"{device_id}prv{private_key}"
                    public_key_format = f"{device_id}pub{public_key}"
                    public_key = public_key_format
                    if db.DevicesDB.add_device(private_key_format, public_key_format, note, device_id):
                        current_user1.add_device(public_key_format, name='Automatic-Link', can_admin=1)
                        response.headers['wpl-key'] = private_key_format
                        response.response = 'OK'
                else:
                    current_user1.add_device(public_key, name='Automatic-Link', can_admin=1)
                    response.response = 'OK'
                if response.response == 'OK':
                    try:
                        device_type = 'Water Level S1 Sensor'
                        if dtype == 3:
                            device_type = 'Smart Pump Controller S1'
                        email_tools.send_device_added(user_data.email, public_key, device_type)
                    except Exception as ex:
                        logging.exception(ex)
    return response


@app.route('/relay_view_api', methods=["GET", "POST"])
def relay_view_api():
    if request.method == "GET":
        key = request.args.get('public_key')

        if key == "demorelay":
            key = settings.DEMO_RELAY_PUB_KEY

        cache_key = f'relay-keys/{key}'
        relay_status = redis_client.get(cache_key)
        status, rtime, rssi = 0, 0, 0
        if relay_status:
            status, rtime, rssi = map(int, relay_status.split('|'))

        events_list = []
        try:
            cache_key_event = f'relay-events/{key}'
            LIVE_EVENTS = redis_client.get(cache_key_event)
            redis_client.delete(cache_key_event)
            if LIVE_EVENTS:
                LIVE_EVENTS = LIVE_EVENTS.strip().split(",")
                for item in LIVE_EVENTS:
                    if int(item) != 0:
                        events_list.append(RELAY_EVENTS_CODE[int(item)][1])
        except Exception as ex:
            logging.exception(ex)
            LIVE_EVENTS = None

        diff_time = int(time.time()) - int(rtime)
        data = {
            "status": status,
            "rtime": rtime,
            "diff_time": diff_time,
            "rssi": rssi,
            "events": events_list
        }
        return jsonify(data)
    elif request.method == "POST":
        public_key = request.form.get("public_key")

        # update case
        if request.form.get("action") in ["on", "off"]:
            set_relay_action(public_key, 1 if request.form.get("action") == "on" else -1)
            return jsonify({'status': "success"})
        return jsonify({'status': "fail unknown action"})


@app.route('/sensor_view_api', methods=["GET"])
def sensor_view_api():
    # Define your title and SEO tags here
    key = request.args.get('public_key')

    if key == "demo":
        key = settings.DEMO_S1_PUB_KEY

    cache_key = f'tin-keys/{key}'
    result = redis_client.get(cache_key)
    distance = 0
    rtime = 0
    rssi = 0
    diff_time = 0
    voltage = 0
    if result:
        distance, rtime, voltage, rssi = result.split("|")
        voltage = float(voltage) / 100.0
        diff_time = int(time.time()) - int(rtime)

    data = {
        "distance": distance,
        "rtime": rtime,
        "skey": key,
        "diff_time": diff_time,
        "voltage": voltage,
        "rssi": rssi
    }

    return jsonify(data)


@app.route('/update')
def update():
    # Get the 'key' parameter from the query string
    private_key = request.args.get('key')
    public_key = db.DevicesDB.valid_private_key(private_key)
    if not public_key:
        return jsonify({'error': 'invalid private key'}), 404
    key = public_key
    logging.warning(f"public_key: {public_key}")
    distance = request.args.get('distance')
    voltage = request.args.get('voltage')
    logging.warning(f"update params: >>> {distance}|{int(time.time())}|{voltage}")
    if not distance:
        return 'ERROR'
    if not voltage:
        return 'ERROR'

    rssi = int(request.headers.get('RSSI', 0))
    device_id = db.DevicesDB.load_device_id_by_public_key(public_key)

    cache_key_uptime = f'key-uptime/{device_id}/{datetime.now().hour}'
    uptime_result = redis_client.get(cache_key_uptime)
    if not uptime_result:
        # 2 hours expire time
        redis_client.set(cache_key_uptime, "true", ex=7200)
        db.DevicesDB.record_uptime(device_id)

    min_updates = 30
    can_update = False

    cache_key = f'tin-keys/{key}'
    result = redis_client.get(cache_key)
    distance_old = 0
    rtime_old = 0
    rssi_old = 0
    voltage_old = 0
    diff_time_old = 0
    if result:
        distance_old, rtime_old, voltage_old, rssi_old = result.split("|")
        diff_time_old = int(time.time()) - int(rtime_old)

        if diff_time_old + 5 < min_updates:
            logging.warning(f"frequency violation at device: {device_id}")
            can_update = False
        else:
            can_update = True
    else:
        can_update = True

    if can_update:
        cache_key = f'tin-keys/{key}'
        redis_client.set(cache_key, f"{distance}|{int(time.time())}|{voltage}|{rssi}")
    else:
        logging.warning(f"This device can't update, id: {device_id}")

    logging.warning(f"FW Version: {request.headers.get('FW-Version', 'unknow')}")
    logging.warning(f"RSSI: {request.headers.get('RSSI', 'unknow')} dBm")

    response = app.response_class(
        response='OK',
        status=200,
        mimetype='text/plain'
    )
    response.headers['fw-version'] = f"{LAST_SENSOR_FW_VERSION}"

    db_device_settings = db.DevicesDB.load_device_settings(device_id=device_id, device_type=1)
    if db_device_settings.WIFI_POOL_TIME < 120 and min_updates == 120:
        db.DevicesDB.update_sensor_pool_time(device_id, 120)
        logging.warning(f"Updating sensor_pool_time for Device: {device_id}, pool_time: {min_updates}")
    if db_device_settings.WIFI_POOL_TIME < 30 and min_updates == 30:
        db.DevicesDB.update_sensor_pool_time(device_id, 30)
        logging.warning(f"Updating sensor_pool_time for Device: {device_id}, pool_time: {min_updates}")
    # WiFi-Pool-Time >> wpl
    response.headers['wpl'] = f"{db_device_settings.WIFI_POOL_TIME}"

    return response


@app.route('/relay-update', methods=["GET"])
def relay_update():
    # Get the 'key' parameter from the query string
    private_key = request.args.get('key')
    public_key = db.DevicesDB.valid_private_key(private_key)
    if not public_key:
        return jsonify({'error': 'invalid private key'}), 404
    key = public_key
    logging.warning(f"public_key: {public_key}")

    rssi = int(request.headers.get('RSSI', 0))

    status = request.args.get('status')
    logging.warning(f"relay params: >>> {key}|{status}|{rssi}")

    cache_key = f'relay-keys/{key}'
    redis_client.set(cache_key, f"{status}|{int(time.time())}|{rssi}")

    logging.warning(f"Relay-FW Version: {request.headers.get('FW-Version', 'unknow')}")
    logging.warning(f"Relay-RSSI: {request.headers.get('RSSI', 'unknow')} dBm")
    logging.warning(f"Relay-EVENTS: {request.headers.get('EVENTS', '')}")
    RELAY_EVENTS = request.headers.get('EVENTS', '')
    if RELAY_EVENTS and RELAY_EVENTS == "0,0,0,0,0":
        RELAY_EVENTS = ''

    sensor_key = 'none'
    device_id = db.DevicesDB.load_device_id_by_public_key(public_key)
    db_device_settings = db.DevicesDB.load_device_settings(device_id=device_id, device_type=3)
    if not db_device_settings:
        logging.error(f"relay don't have settings, public_key: {public_key}")

    if DEVELOPER_MODE and RELAY_EVENTS:
        db.DevicesDB.add_relay_events(device_id, RELAY_EVENTS)
        cache_key_event = f'relay-events/{key}'
        redis_client.set(cache_key_event, RELAY_EVENTS)
        RELAY_EVENTS = RELAY_EVENTS.split(",")

    if RELAY_EVENTS and ('2' in RELAY_EVENTS or '14' in RELAY_EVENTS):
        logging.warning(f"Detected sensor fail or danger blind distance, for device: {device_id}")
        db.DevicesDB.turn_off_relay_smart_mode(device_id)

    sensor_key = db_device_settings.SENSOR_KEY
    raction = get_relay_action(public_key)
    # relay action read by device, pass to neutral
    set_relay_action(public_key, action=0)

    response = app.response_class(
        response='OK',
        status=200,
        mimetype='text/plain'
    )
    response.headers['percent'] = 0
    response.headers['event-time'] = 0
    response.headers['current-time'] = 0
    response.headers['fw-version'] = LAST_RELAY_FW_VERSION
    response.headers['pool-time'] = 0

    response.headers['ALGO'] = db_device_settings.ALGO
    response.headers['SAFE_MODE'] = db_device_settings.SAFE_MODE
    response.headers['START_LEVEL'] = db_device_settings.START_LEVEL
    response.headers['END_LEVEL'] = db_device_settings.END_LEVEL
    response.headers['AUTO_OFF'] = db_device_settings.AUTO_OFF
    response.headers['AUTO_ON'] = db_device_settings.AUTO_ON
    response.headers['MIN_FLOW_MM_X_MIN'] = db_device_settings.MIN_FLOW_MM_X_MIN
    response.headers['ACTION'] = raction
    response.headers['BLIND_DISTANCE'] = db_device_settings.BLIND_DISTANCE
    response.headers['HOURS_OFF'] = db_device_settings.HOURS_OFF or '-'

    if sensor_key != 'none' and sensor_key:
        cache_key = f'tin-keys/{sensor_key}'
        sensor_data = redis_client.get(cache_key)

        distance = 0
        rtime = 0
        if sensor_data:
            distance, rtime, voltage, rssi = sensor_data.split("|")

        device_id = db.DevicesDB.load_device_id_by_public_key(sensor_key)
        db_device_settings = db.DevicesDB.load_device_settings(device_id=device_id, device_type=1)

        EMPTY_LEVEL = db_device_settings.EMPTY_LEVEL
        TOP_MARGIN = db_device_settings.TOP_MARGIN
        WIFI_POOL_TIME = db_device_settings.WIFI_POOL_TIME
        percent = 0
        if db_device_settings:
            distance = int(distance)

            if EMPTY_LEVEL == 0:
                EMPTY_LEVEL = 1
            percent = min(100, 100 - min(100, int(((distance - TOP_MARGIN) * 100.0) / ((EMPTY_LEVEL - TOP_MARGIN)))))

            response.headers['percent'] = int(percent)
            response.headers['event-time'] = int(rtime)
            response.headers['current-time'] = int(time.time())
            response.headers['distance'] = int(distance)
            response.headers['pool-time'] = int(WIFI_POOL_TIME)

    return response


def get_relay_action(public_key):
    # 0-neutral, 1-on, -1-off
    rkey = f'relay_action/{public_key}'
    raction = redis_client.get(rkey)
    if raction:
        return int(raction)
    return 0


def set_relay_action(public_key, action=1):
    # 0-neutral, 1-on, -1-off
    rkey = f'relay_action/{public_key}'
    redis_client.set(rkey, action)


if __name__ == '__main__':
    #app.run(ssl_context=('cert.pem', 'key.pem'), host='0.0.0.0', port=443, debug=True)
    app.run(debug=True, port=88)

