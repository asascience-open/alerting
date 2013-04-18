from bson.objectid import ObjectId
from datetime import timedelta, datetime

from alerting import app, db, scheduler
from alerting.models.condition import Condition
from rq import get_current_job

def check(alert_id):
    with app.app_context():

        job = get_current_job()

        app.logger.debug("Running alert job for %s" % alert_id)

        alert = db.Alert.find_one({ '_id' : ObjectId(alert_id) })
        if alert is None:
            app.logger.debug("No Alert found with that ID, cancelling job")
            scheduler.cancel(job)
            return False
            
        data_to_send = alert.check()

        if isinstance(alert.sent, datetime):
            can_send_next = alert.sent + timedelta(minutes=alert.frequency)
        else:
            can_send_next = datetime.fromtimestamp(0)

        # Only send email if the alert is active and we have not sent 
        # an email within the requested frequency already.
        if not alert.active:
            app.logger.debug("Alert NOT sent.  Is not active.")
            return False

        if len(data_to_send) < 1:
            app.logger.debug("Alert NOT sent.  No condition matched.")
            return False

        if datetime.utcnow() < can_send_next:
            app.logger.debug("Alert NOT sent.  Already sent within frequency.")
            return False

        # Send email
        app.logger.debug("Alert sent")
        app.logger.debug(data_to_send)

        alert.sent = datetime.utcnow()
        alert.save()
            
    return True