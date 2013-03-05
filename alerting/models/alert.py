from datetime import datetime, timedelta
from bson.objectid import ObjectId

from ago import human

from flask.ext.mongokit import Document

from alerting import db
from alerting.models.condition import Condition

from shapely.wkt import loads
from shapely.geometry import Point

class Alert(Document):
    __collection__ = 'alerts'
    use_autorefs = True
    use_schemaless = True
    use_dot_notation = True
    structure = {
        'name'              : unicode,      # Name of the dataset
        'email'             : unicode,      # Email of the user who created the alert
        'conditions'        : [Condition],
        'created'           : datetime,     # when this alert was created
        'updated'           : datetime, 
        'checked'           : datetime,     # last time all of the conditions were checked
        'sent'              : datetime,     # last time an alert was sent
        'frequency'         : int           # number of minutes between alerts
    }
    required_fields = ['email', 'created', 'updated', 'frequency']
    default_values = { 'name': u'Unnamed Alert', 'created': datetime.utcnow, 'updated' : datetime.utcnow, 'frequency' : 15 }

    def user_friendly_frequency(self):
        if self.frequency:
            return human(timedelta(minutes=self.frequency), past_tense='{}')
        else:
            return "never"

    def user_friendly_checked(self):
        if self.checked:
            return human(datetime.utcnow() - self.checked)
        else:
            return "never"

db.register([Alert])