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
        'buffer'            : int,          # number of minutes conditions need to occur in to alert
        'active'            : bool          # If alerts should be SENT
    }
    required_fields = ['email', 'created', 'updated', 'frequency', 'buffer']
    default_values = { 'name': u'UnnamedAlertGroup', 'created': datetime.utcnow, 'updated' : datetime.utcnow, 'frequency' : 60, 'active' : True, 'buffer' : 60 }

    def user_friendly_frequency(self):
        return human(timedelta(minutes=self.frequency), precision=1, past_tense='{}')

    def user_friendly_buffer(self):
        return human(timedelta(minutes=self.buffer), precision=1, past_tense='{}')

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

        data_to_send = {}

        for condition in self.conditions:
            try:
                # Make sure comparator is valid 
                assert condition.comparator in Condition.COMPARATORS
            except:
                # Invalid condition, remove it.
                app.logger.debug("Removing invalid condition")
                condition.delete()
            else:

                date_and_values = []
                if self.checked:
                    check_time = self.checked - timedelta(minutes=self.buffer)
                else:
                    check_time = datetime.utcnow() - timedelta(minutes=self.buffer)

                date_and_values = [(t,d) for t,d in condition.times_and_data() if t >= check_time]

                to_send = condition.check(date_and_values)

                if len(to_send) > 0:
                    # Set to the last measured time that met the condition                    
                    condition.triggered = to_send[-1][0]
                    condition.save()

                    detached_condition = copy(condition)

                    # Set some helper vars
                    stat = condition.station()
                    del detached_condition["station_id"]
                    del detached_condition["_id"]

                    detached_condition["values"] = to_send

                    if not data_to_send.has_key(unicode(stat._id)):
                        data_to_send[unicode(stat._id)] = { 
                            'name'          : stat.provider + "-" + stat.description,
                            'link'          : stat.link,
                            'conditions'    : []
                        }

                    data_to_send[unicode(stat._id)]['conditions'].append(detached_condition)

        self.checked = datetime.utcnow()
        self.save()

        return data_to_send

db.register([Alert])