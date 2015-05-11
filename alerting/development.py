import os

DEBUG = True

REDIS_URL = os.getenv('REDIS_URI')

# Database
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
MONGODB_DATABASE = 'alerting_production'
