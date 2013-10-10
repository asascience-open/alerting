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
        'updated'           : datetime,
        'triggered'         : datetime  # The last time the condition was met
    }
    required_fields = ['station_id', 'comparator', 'value', 'created', 'updated', 'variable', 'units']
    default_values = { 'created': datetime.utcnow, 'updated': datetime.utcnow }

    COMPARATORS = ["<", "=", ">"]
    CMP_RETURNS = [-1,   0,   1]

    def station(self):
        return db.Station.find_one({ '_id' : self.station_id })

    def times_and_data(self):
        return self.station().times_and_data(variable=self.variable, units=self.units)

    def check(self, date_value_tuples):
        # Get the return value that cmp should return for the comparator
        comparator_value = Condition.CMP_RETURNS[Condition.COMPARATORS.index(self.comparator)]
        triggering = filter(lambda (t,d): cmp(d, self.value) == comparator_value, date_value_tuples)
        return triggering

    def label(self):
        return "%s (%s) %s %d" % (self.variable, self.units, self.comparator, self.value)

db.register([Condition])
