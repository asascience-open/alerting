from datetime import datetime
from bson.objectid import ObjectId

from flask.ext.mongokit import Document

from alerting import db

class Condition(Document):
    __collection__ = 'conditions'
    use_autorefs = True
    use_schemaless = True
    use_dot_notation = True
    structure = {
        'station_id'        : ObjectId,
        'variable'          : unicode,
        'units'             : unicode,
        'comparator'        : unicode,
        'value'             : float,
        'created'           : datetime,
        'updated'           : datetime
    }
    required_fields = ['station_id', 'comparator', 'value', 'created', 'updated', 'variable', 'units']
    default_values = { 'created': datetime.utcnow, 'updated': datetime.utcnow }

    COMPARATORS = [">=", "<=", "="]

    def station(self):
        return db.Station.find_one({ '_id' : self.station_id })

    def data(self):
        return self.station().data(variable=self.variable, units=self.units)

db.register([Condition])
