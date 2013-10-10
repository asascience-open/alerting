from flask import Flask
from flask.ext.mongokit import MongoKit
from flask.ext.oauth import OAuth
from flask.ext.login import LoginManager
from flask.ext.mail import Mail

# Create application object
app = Flask(__name__)

app.config.from_object('alerting.defaults')
app.config.from_envvar('APPLICATION_SETTINGS', silent=True)

# Create logging
if app.config.get('LOG_FILE') == True:
    import logging
    from logging import FileHandler
    file_handler = FileHandler('log.txt')
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

oauth = OAuth()

facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=app.config.get('FACEBOOK_APP_ID'),
    consumer_secret=app.config.get('FACEBOOK_APP_SECRET'),
    request_token_params={'scope': 'email'}
    )
google = oauth.remote_app('google',
    base_url='https://www.google.com/accounts/',
    request_token_url=None,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    consumer_key=app.config.get('GOOGLE_CLIENT_ID'),
    consumer_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
    access_token_method='POST',
    request_token_params={'response_type':'code','scope':'https://www.googleapis.com/auth/userinfo.email'},
    access_token_params={'grant_type':'authorization_code'}
)

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

