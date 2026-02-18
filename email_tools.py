import hmac
import hashlib

import smtplib
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import EmailMessage
from flask_babel import _

from settings import EMAIL_SENDER, SMTP_PORT, SMTP_SERVER, SMTP_TEST, APP_SEC_KEY, APP_DOMAIN
from urllib.parse import quote


def send_device_added(to_email, public_key, device_type='Water Level S1 Sensor'):
    confirmation_code = generate_confirmation_code(to_email)
    encoded_email = quote(to_email)

    # Create the message
    message = EmailMessage()
    message["Subject"] = f"{device_type} linked to your account!"
    message["From"] = EMAIL_SENDER
    message["To"] = to_email

    alert_body_text = f""" <h2>{device_type} successfully linked to your account!</h2>
                    <p>
                        Here can monitor your device: 
                        <a href='{APP_DOMAIN}/device_info?public_key={public_key}' target='_blank' >Device Monitor Link<a/>
                        <br>
                        <a href='{APP_DOMAIN}' target='_blank' >Login<a/> to your account for adjust device settings.
                    </p>
                    """

    alert_body_html = f""" <h2>{device_type} successfully linked to your account!</h2>
                <p>
                    Here can monitor your device: 
                    <a href='{APP_DOMAIN}/device_info?public_key={public_key}' target='_blank' >Device Monitor Link<a/>
                    <br>
                    <a href='{APP_DOMAIN}' target='_blank' >Login<a/> to your account for adjust device settings.
                </p>
                """

    # Create a plain text alternative for email clients that don't support HTML
    message.set_content(f"""\
                {alert_body_text}

                WaterLevel.Pro Services
            """)

    # Create the HTML content
    message.add_alternative(f"""\
            <html>
              <body>
                {alert_body_html}
                <p>
                    Best Regards,<br>
                    <a href='{APP_DOMAIN}' target='_blank' >
                        WaterLevel.Pro Services
                    <a/>
                </p>
              </body>
            </html>
            """, subtype='html')

    if SMTP_TEST:
        print(message)
        return

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.send_message(message)
        server.quit()


def send_register_email(to_email, lang='en'):
    confirmation_code = generate_confirmation_code(to_email)
    encoded_email = quote(to_email)

    # Create the message
    message = EmailMessage()
    message["Subject"] = _("Register Confirm [WaterLevel.Pro]")
    message["From"] = EMAIL_SENDER
    message["To"] = to_email

    # Marcar todas las cadenas traducibles por separado
    welcome_msg = _("Welcome to WaterLevel.Pro Services!")
    open_link_msg = _("Open this link")
    confirm_msg = _("to confirm your WaterLevel.Pro account.")
    regards_msg = _("Best Regards,")

    # Create a plain text alternative for email clients that don't support HTML
    message.set_content(f"""
            {welcome_msg}

            {open_link_msg} {APP_DOMAIN}/user-confirm?code={confirmation_code}&email={encoded_email} {confirm_msg}

            {regards_msg}
            WaterLevel.Pro
        """)

    # Create the HTML content
    message.add_alternative(f"""\
        <html>
          <body>
            <h4>{welcome_msg}</h4>
            
            <p>
            <a href='{APP_DOMAIN}/user-confirm?code={confirmation_code}&email={encoded_email}' target='_blank' > 
                {open_link_msg} </a> {confirm_msg}
            </p>
            <p>
                {regards_msg}<br>
                <a href='{APP_DOMAIN}/user-confirm?code={confirmation_code}&email={encoded_email}' target='_blank' >
                    WaterLevel.Pro
                <a/>
            </p>
          </body>
        </html>
        """, subtype='html')

    if SMTP_TEST:
        print(message)
        return

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.send_message(message)
        server.quit()


def send_alert_email(to_email, alert_subject, alert_body):
    confirmation_code = generate_confirmation_code(to_email)
    encoded_email = quote(to_email)

    # Create the message
    message = EmailMessage()
    message["Subject"] = alert_subject
    message["From"] = EMAIL_SENDER
    message["To"] = to_email

    # Create a plain text alternative for email clients that don't support HTML
    message.set_content(f"""\
            {alert_body}

            WaterLevel.Pro Services
        """)

    # Create the HTML content
    message.add_alternative(f"""\
        <html>
          <body>
            {alert_body}
            <p>
                <a href='{APP_DOMAIN}' target='_blank' >Login<a/> to your account for adjust email alert settings.
            </p>
            <p>
                Best Regards,<br>
                <a href='{APP_DOMAIN}' target='_blank' >
                    WaterLevel.Pro Services
                <a/>
            </p>
          </body>
        </html>
        """, subtype='html')

    if SMTP_TEST:
        print(message)
        return

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.send_message(message)
        server.quit()


def generate_confirmation_code(to_email):
    to_email = to_email.encode()
    return hmac.new(APP_SEC_KEY.encode(), to_email, hashlib.sha256).hexdigest()


def check_confirmation_code(to_email, hmac_digest):
    to_email = to_email.encode()
    hmac_digest = hmac_digest.encode()
    hmac_sha256_verifier = hmac.new(APP_SEC_KEY.encode(), to_email, hashlib.sha256)
    if hmac.compare_digest(hmac_digest, hmac_sha256_verifier.hexdigest().encode()):
        return True
    return False


def support_email(to_email, message_reply):
    confirmation_code = generate_confirmation_code(to_email)
    encoded_email = quote(to_email)

    # Create the message
    message = EmailMessage()
    message["Subject"] = "Support [WaterLevel.Pro]"
    message["From"] = '"WaterLevel.Pro Support" <support@waterlevel.pro>'
    message["To"] = to_email

    # Create a plain text alternative for email clients that don't support HTML
    message.set_content(f"""\
            WaterLevel.Pro Support Reply:
            
            {message_reply}

            Best Regards,
            WaterLevel.Pro Support
        """)

    # Create the HTML content
    message.add_alternative(f"""\
        <html>
          <body>
            <h4>WaterLevel.Pro Support Reply:</h4>
            {message_reply}
            
            <div>
                Best Regards,<br>
                <a href='{APP_DOMAIN}/contact' target='_blank' >
                    WaterLevel.Pro
                <a/>
            </div>
          </body>
        </html>
        """, subtype='html')

    if SMTP_TEST:
        print(message)
        return

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.send_message(message)
        server.quit()


if __name__ == "__main__":
    send_device_added("user@example.com", "PUBLIC_KEY_EXAMPLE")
