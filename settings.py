import os


def env_bool(name, default=False):
    """Read an environment variable and coerce it to boolean.

    Accepted truthy values are: `1`, `true`, `yes`, `on` (case-insensitive).

    Args:
        name: Environment variable name to read.
        default: Fallback value used when the variable is missing.

    Returns:
        bool: Parsed boolean value from environment or fallback.
    """
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


def env_str(name, default=""):
    """Read env var as string, treating empty values as missing.

    Args:
        name: Environment variable name to read.
        default: Fallback value used when var is missing/empty.

    Returns:
        str: Trimmed env value or fallback default.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip()
    return value if value else default


DEV_MODE = env_bool("DEV_MODE", True)

#  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# APP Settings
APP_SEC_KEY = os.getenv("APP_SEC_KEY", "CHANGE_ME_IN_PRODUCTION")
APP_RECAPTCHA_SECRET_KEY = os.getenv("APP_RECAPTCHA_SECRET_KEY", "")
RECAPTCHA_PUBLIC_KEY = os.getenv("RECAPTCHA_PUBLIC_KEY", "")
WLP_BASE_DOMAIN = env_str("WLP_BASE_DOMAIN", "localhost")
WLP_API_SUBDOMAIN = env_str("WLP_API_SUBDOMAIN", "api")
WLP_TZ = env_str("WLP_TZ", "America/Santo_Domingo")

WLP_SERVER_NAME = env_str("WLP_SERVER_NAME", WLP_BASE_DOMAIN)
default_api_server_name = (
    WLP_BASE_DOMAIN if WLP_API_SUBDOMAIN in {"", "@"} else f"{WLP_API_SUBDOMAIN}.{WLP_BASE_DOMAIN}"
)
WLP_API_SERVER_NAME = env_str("WLP_API_SERVER_NAME", default_api_server_name)

APP_DOMAIN = env_str("APP_DOMAIN", f"https://{WLP_SERVER_NAME}")
API_DOMAIN = env_str("API_DOMAIN", f"https://{WLP_API_SERVER_NAME}")
WLP_ENABLE_TRACKING = env_bool("WLP_ENABLE_TRACKING", False)
WLP_GA_MEASUREMENT_ID = os.getenv("WLP_GA_MEASUREMENT_ID", "")
WLP_TWITTER_PIXEL_ID = os.getenv("WLP_TWITTER_PIXEL_ID", "")
WLP_ENABLE_ADSENSE = env_bool("WLP_ENABLE_ADSENSE", False)
WLP_ADSENSE_CLIENT_ID = os.getenv("WLP_ADSENSE_CLIENT_ID", "")

#  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# SMTP Settings
SMTP_TEST = env_bool("SMTP_TEST", DEV_MODE)
EMAIL_SENDER = os.getenv("EMAIL_SENDER", '"Water Level .Pro" <no-reply@example.com>')
SMTP_SERVER = os.getenv("SMTP_SERVER", "127.0.0.1")
SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_STARTTLS = env_bool("SMTP_USE_STARTTLS", True)
SMTP_USE_SSL = env_bool("SMTP_USE_SSL", False)
SMTP_TIMEOUT_SECONDS = int(os.getenv("SMTP_TIMEOUT_SECONDS", "20"))
#  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# API CACHE Settings
API_CACHE_SETT = {
    "CACHE_REDIS_HOST": os.getenv("API_CACHE_REDIS_HOST", "127.0.0.1"),
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": int(os.getenv("API_CACHE_DEFAULT_TIMEOUT", "30")),
    "CACHE_REDIS_DB": 2
}
#  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# WEB APP CACHE Settings
WEB_CACHE_SETT = {
    "CACHE_REDIS_HOST": os.getenv("WEB_CACHE_REDIS_HOST", "127.0.0.1"),
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": int(os.getenv("WEB_CACHE_DEFAULT_TIMEOUT", "30")),
    "CACHE_REDIS_DB": 1
}
#  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER", "")

# ++++++++++++++++

DEMO_S1_PUB_KEY = os.getenv("DEMO_S1_PUB_KEY", "1pubDEMO_SENSOR_S1")
DEMO_S1_PRV_KEY = os.getenv("DEMO_S1_PRV_KEY", "1prvDEMO_SENSOR_S1")
DEMO_RELAY_PUB_KEY = os.getenv("DEMO_RELAY_PUB_KEY", "3pubDEMO_RELAY_R1")
DEMO_RELAY_PRV_KEY = os.getenv("DEMO_RELAY_PRV_KEY", "3prvDEMO_RELAY_R1")

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
WEB_REDIS_DB = 0
API_REDIS_DB = 0

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db?journal_mode=WAL2")

REPORTS_FOLDER = './reports/'