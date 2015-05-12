from flask import Flask
from flask.ext.mongokit import MongoKit
from flask.ext.oauth import OAuth
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from flask_environments import Environments

# Create application object
app = Flask(__name__)
env = Environments(app)
env.from_yaml('config.yml')


# Create logging
if app.config.get('LOG_FILE') == True:
    import logging
    from logging import FileHandler
    file_handler = FileHandler('log.txt')
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

# Create the database connection
db = MongoKit(app)

# Create the Redis connection
import redis
from rq import Queue
redis_connection = redis.from_url(app.config.get("REDIS_URL"))
queue = Queue('default', connection=redis_connection, default_timeout=600)

from rq_scheduler import Scheduler
scheduler = Scheduler(queue_name="default", connection=redis_connection)

# Setup RQ Dashboard
from rq_dashboard import RQDashboard
RQDashboard(app)

# Create the Flask-Login manager
login_manager = LoginManager()
from bson.objectid import ObjectId
@login_manager.user_loader
def load_user(userid):
    return db.User.find_one({ '_id' : ObjectId(userid) })
login_manager.init_app(app)

# Create the Flask-Mail object
mail = Mail(app)

from datetime import datetime, tzinfo
import pytz
# Create datetime jinja2 filter
def datetimeformat(value, format='%a, %b %d %Y at %I:%M%p', tz=None):
    if isinstance(value, datetime):
        if tzinfo is not None and isinstance(tz, tzinfo):
            if value.tzinfo is None:
                value = value.replace(tzinfo=pytz.utc)
            return value.astimezone(tz).strftime(format)
        else:
            return value.strftime(format)
    return value
app.jinja_env.filters['datetimeformat'] = datetimeformat

# Import everything
import alerting.views
import alerting.models
import alerting.tasks

