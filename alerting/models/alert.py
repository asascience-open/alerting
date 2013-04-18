from datetime import datetime, timedelta
from bson.objectid import ObjectId
from copy import copy

from ago import human

from flask.ext.mongokit import Document

from alerting import db, app
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
        'frequency'         : int,          # number of minutes between alerts
        'active'            : bool          # If alerts should be SENT
    }
    required_fields = ['email', 'created', 'updated', 'frequency']
    default_values = { 'name': u'Unnamed Alert', 'created': datetime.utcnow, 'updated' : datetime.utcnow, 'frequency' : 60, 'active' : True }

    def user_friendly_frequency(self):
        if self.frequency:
            return human(timedelta(minutes=self.frequency), precision=1, past_tense='{}')
        else:
            return "never"

    def user_friendly_checked(self):
        if self.checked:
            return human(datetime.utcnow() - self.checked, precision=1)
        else:
            return "never"

    def user_friendly_sent(self):
        if self.sent:
            return human(datetime.utcnow() - self.sent, precision=1)
        else:
            return "never"

    def check(self):

        data_to_send = []

        for condition in self.conditions:
            try:
                # Make sure comparator is valud 
                assert condition.comparator in Condition.COMPARATORS
            except:
                # Invalid condition, remove it.
                app.logger.debug("Removing invalid condition")
                condition.delete()
            else:

                date_and_values = []
                if self.checked:
                    date_and_values = [(t,d) for t,d in condition.times_and_data() if t > self.checked]
                else:
                    date_and_values = condition.times_and_data()

                to_send = condition.check(date_and_values)

                if len(to_send) > 0:
                    # Set to the last measured time that met the condition                    
                    condition.triggered = to_send[-1][0]
                    condition.save()

                    detached_condition = copy(condition)

                    # Set some helper vars
                    detached_condition["station"] = db.Station.find_one({ '_id' : condition._id })
                    del detached_condition["station_id"]
                    del detached_condition["_id"]

                    data_to_send.append({
                        'condition' : detached_condition,
                        'data'      : to_send 
                    })

        self.checked = datetime.utcnow()
        self.save()

        return data_to_send

db.register([Alert])