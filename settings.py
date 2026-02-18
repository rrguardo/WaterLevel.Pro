import os


def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


DEV_MODE = env_bool("DEV_MODE", True)

#  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# APP Settings
APP_SEC_KEY = os.getenv("APP_SEC_KEY", "CHANGE_ME_IN_PRODUCTION")
APP_RECAPTCHA_SECRET_KEY = os.getenv("APP_RECAPTCHA_SECRET_KEY", "")
RECAPTCHA_PUBLIC_KEY = os.getenv("RECAPTCHA_PUBLIC_KEY", "")
APP_DOMAIN = os.getenv("APP_DOMAIN", "http://localhost")
API_DOMAIN = os.getenv("API_DOMAIN", "http://api.localhost")

#  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# SMTP Settings
SMTP_TEST = env_bool("SMTP_TEST", DEV_MODE)
EMAIL_SENDER = os.getenv("EMAIL_SENDER", '"Water Level .Pro" <no-reply@example.com>')
SMTP_SERVER = os.getenv("SMTP_SERVER", "127.0.0.1")
SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
#  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# API CACHE Settings
API_CACHE_SETT = {
    "CACHE_REDIS_HOST": os.getenv("API_CACHE_REDIS_HOST", "127.0.0.1"),
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": int(os.getenv("API_CACHE_DEFAULT_TIMEOUT", "30")),
    "CACHE_REDIS_DB": int(os.getenv("API_CACHE_REDIS_DB", "2"))
}
#  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# WEB APP CACHE Settings
WEB_CACHE_SETT = {
    "CACHE_REDIS_HOST": os.getenv("WEB_CACHE_REDIS_HOST", "127.0.0.1"),
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": int(os.getenv("WEB_CACHE_DEFAULT_TIMEOUT", "30")),
    "CACHE_REDIS_DB": int(os.getenv("WEB_CACHE_REDIS_DB", "1"))
}
#  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER", "")

# ++++++++++++++++

DEMO_S1_PUB_KEY = os.getenv("DEMO_S1_PUB_KEY", "")
DEMO_RELAY_PUB_KEY = os.getenv("DEMO_RELAY_PUB_KEY", "")

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
WEB_REDIS_DB = int(os.getenv("WEB_REDIS_DB", "0"))
API_REDIS_DB = int(os.getenv("API_REDIS_DB", "3"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db?journal_mode=WAL2")

REPORTS_FOLDER = './reports/'