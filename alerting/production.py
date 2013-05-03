import os
import urlparse

REDIS_URL = os.getenv('REDIS_URI')

mongo_uri = os.environ.get('MONGO_URI')
url = urlparse.urlparse(mongo_uri)
# Database
MONGODB_HOST = url.hostname
MONGODB_PORT = url.port
MONGODB_DATABASE = url.path[1:]