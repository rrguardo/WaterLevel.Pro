import requests
import sys

# Define the URL and parameters
DOMAIN = 'http://127.0.0.1:88' #'http://waterlevel.pro:88'  # 'http://127.0.0.1:5000'
DOMAIN = 'https://api.waterlevel.pro'

def simulate_sensor_post(device_key, distance, voltage):
    """Send a simulated sensor update request to the API `/update` endpoint.

    Args:
        device_key: Sensor private key used by firmware updates.
        distance: Simulated measured distance in centimeters.
        voltage: Simulated battery voltage in centivolts.

    Returns:
        None.
    """
    params = {'key': device_key, 'distance': distance, 'voltage': voltage}

    # "%d|%d|%d|%d|%d", EMPTY_LEVEL, TOP_MARGIN, WIFI_POOL_TIME, SONIC_POOL_TIME, (int)CurrentStatus
    EMPTY_LEVEL = 120
    TOP_MARGIN = 15
    WIFI_POOL_TIME = 10
    SONIC_POOL_TIME = 2
    CurrentStatus = 1 # wifi
    sett = f"{EMPTY_LEVEL}|{TOP_MARGIN}|{WIFI_POOL_TIME}|{SONIC_POOL_TIME}|{CurrentStatus}"

    url = DOMAIN + "/update"
    #url = "http://127.0.0.1/demo_server"

    headers = {
        "RSSI": "-70",
        "Settings-Header": sett,
        "FW-Version": "10"
    }
    response = requests.get(url, params=params, headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Print the response content
        print(response.text)
    else:
        print('Request failed with status code:', response.status_code)
        print('Body: ' + response.text)


def simulate_relay_post(device_key, status=0):
    """Send a simulated relay update request to the API `/relay-update` endpoint.

    Args:
        device_key: Relay private key used by firmware updates.
        status: Relay state value (`0` off, `1` on).

    Returns:
        None.
    """
    params = {'key': device_key, 'status': status}

    # "%d|%d|%d|%d|%d|%d|%s|%d", ALGO, START_LEVEL, END_LEVEL, AUTO_OFF, AUTO_ON, MIN_FLOW_MM_X_MIN, SensorKey.c_str(), ACTION);
    ALGO = 120
    START_LEVEL = 15
    END_LEVEL = 10
    AUTO_OFF = 1
    AUTO_ON = 1
    MIN_FLOW_MM_X_MIN = 1 # wifi
    SENSOR_KEY = 'fsdfs'
    ACTION = 0
    sett = "%d|%d|%d|%d|%d|%d|%s|%d" % (ALGO, START_LEVEL, END_LEVEL, AUTO_OFF, AUTO_ON, MIN_FLOW_MM_X_MIN, SENSOR_KEY, ACTION)

    url = DOMAIN + "/relay-update"

    headers = {
        "RSSI": "-70",
        "Settings-Header": sett,
        "FW-Version": "10"
    }
    response = requests.get(url, params=params, headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Print the response content
        print(response.text)
    else:
        print('Request failed with status code:', response.status_code)
        print('Body: '+ response.text)
        print(f'HEADERS: {response.headers}')


if __name__ == "__main__":
    device_key = "1prvgXtczEL1p7wtg8S34xld8a"  # << sales1 # demo >> "prvkjs00d12Vf34SrfFer6f35t"
    simulate_sensor_post(device_key, sys.argv[1], 375)
    #simulate_relay_post("relay-wvdl0pfd9s12-1", status=0)
