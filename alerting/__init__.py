from flask import Flask
from flask.ext.mongokit import MongoKit
from flask.ext.oauth import OAuth

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

# Import everything
import alerting.views