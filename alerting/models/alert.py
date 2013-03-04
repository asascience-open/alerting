from datetime import datetime
from bson.objectid import ObjectId

from flask.ext.mongokit import Document

from alerting import db
from alerting.models.condition import Condition

from shapely.wkt import loads
from shapely.geometry import Point

class Alert(Document):
    __collection__ = 'alerts'
    use_schemaless = True
    use_dot_notation = True
    structure = {
        'name'              : unicode,  # Name of the dataset
        'email'             : unicode,  # Email of the user who created the alert
        'conditions'        : [Condition],
        'station_id'        : ObjectId,
        'created'           : datetime,
        'updated'           : datetime,
        'sent'              : datetime
    }
    required_fields = ['email', 'station_id', 'created', 'updated']
    default_values = { 'name': u'Alert', 'created': datetime.utcnow, 'updated' : datetime.utcnow }

    def station(self):
        return db.Station.find_one({ '_id' : self.station_id })

db.register([Alert])
