from datetime import datetime

from flask.ext.mongokit import Document

from alerting import db

class Condition(Document):
    __collection__ = 'conditions'
    use_schemaless = True
    use_dot_notation = True
    structure = {
        'variable'          : unicode,
        'comparator'        : unicode,
        'value'             : float,
        'created'           : datetime,
        'updated'           : datetime,
        'checked'           : datetime
    }
    required_fields = ['comparator', 'value', 'created', 'updated']
    default_values = { 'created': datetime.utcnow, 'updated': datetime.utcnow }

    COMPARATORS = [">=", "<=", "="]

db.register([Condition])
