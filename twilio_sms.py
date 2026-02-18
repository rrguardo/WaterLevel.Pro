import settings
from twilio.rest import Client
import db
import logging


def setup_logger():
    # Configure the logging system
    logging.basicConfig(level=logging.WARNING, handlers=[], format='%(asctime)s - %(levelname)s - %(message)s')  # Do not add the implicit handler
    #formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Create a handler and set the formatter
    #handler = logging.StreamHandler()
    #handler.setFormatter(formatter)

    # Add the handler to the root logger
    #logging.getLogger().addHandler(handler)


setup_logger()


# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = settings.TWILIO_ACCOUNT_SID
auth_token = settings.TWILIO_AUTH_TOKEN
FROM_NUMBER = settings.TWILIO_NUMBER
SMS_RATE = 0.05  # 0.0115
MIN_BALANCE = 0.2

def send_phone_verify_code(user_phone, code):
    client = Client(account_sid, auth_token)
    message = client.messages \
        .create(
        body=f'WaterLevel.Pro CODE: {code}',
        from_=FROM_NUMBER,
        to=user_phone
    )


def send_alert(user_id, user_phone, alert):
    credits = db.User.get_sms_credits(user_id)
    if credits < MIN_BALANCE:
        logging.warning(f"Low SMS credits, user: {user_id} --- credits {credits}")
        return False
    db.User.consume_sms_credits(user_id, SMS_RATE)

    client = Client(account_sid, auth_token)
    message = client.messages \
        .create(
        body=alert[:70] + " -- WaterLevel.Pro Alert!",
        from_=FROM_NUMBER,
        to=user_phone
    )
