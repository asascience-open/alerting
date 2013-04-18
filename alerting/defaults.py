import os

DEBUG = False
TESTING = False
LOG_FILE = bool(os.environ.get("LOG_FILE", False))

WEB_PASSWORD = os.environ.get("WEB_PASSWORD")

SECRET_KEY = os.environ.get('SECRET_KEY')

FACEBOOK_APP_ID = os.environ.get("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.environ.get("FACEBOOK_APP_SECRET")

GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")