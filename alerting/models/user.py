import re
import uuid
from datetime import datetime

from flask.ext.mongokit import Document

from alerting import db, app

from werkzeug import generate_password_hash, check_password_hash

def validate_email(value):
    email = re.compile(r'(?:^|\s)[-a-z0-9_.]+@(?:[-a-z0-9]+\.)+[a-z]{2,6}(?:\s|$)',re.IGNORECASE)
    return bool(email.match(value))

class User(Document):
    __collection__ = 'users'
    use_schemaless = True
    use_dot_notation = True
    raise_validation_errors = True
    structure = {
        'email'             : unicode,
        'password'          : unicode,
        'phone'             : unicode,
        'confirmed'         : bool,
        'confirmation_token': unicode,
        'created'           : datetime
    }
    required_fields = ['email']
    default_values = { 'created' : datetime.utcnow, 'confirmed' : False }
    validators = {
        'email'     : validate_email
    }

    def generate_confirmation_key(self):
        return unicode(uuid.uuid4().hex)

    def generate_password(self, password):
        return unicode(generate_password_hash(password))

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_authenticated(self):
        return self.validate()

    def is_active(self):
        return self.confirmed

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self._id)

db.register([User])
