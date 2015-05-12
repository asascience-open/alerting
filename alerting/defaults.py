import os

DEBUG = False
TESTING = False
LOG_FILE = bool(os.environ.get("LOG_FILE", False))

WEB_PASSWORD = os.environ.get("WEB_PASSWORD")

SECRET_KEY = os.environ.get('SECRET_KEY')

# Email
MAIL_SERVER = os.environ.get("MAIL_SERVER")
MAIL_PORT = os.environ.get("MAIL_PORT")
MAIL_USE_TLS = bool(os.environ.get("MAIL_USE_TLS", True))
MAIL_USE_SSL = bool(os.environ.get("MAIL_USE_SSL", False))
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
MAIL_SENDER = os.environ.get("MAIL_SENDER")
