import pytz

from bson.objectid import ObjectId
from datetime import timedelta, datetime

from rq import get_current_job
from flask import render_template

from alerting import app, db, scheduler
from alerting.models.condition import Condition
from alerting.utils import jsonify, nocache
from alerting.tasks.send_email import send

def check(alert_id):
    with app.test_request_context():

        job = get_current_job()

        app.logger.debug("Running alert job for %s" % alert_id)

        alert = db.Alert.find_one({ '_id' : ObjectId(alert_id) })
        if alert is None:
            app.logger.debug("No Alert found with that ID, cancelling job")
            scheduler.cancel(job)
            return "No Alert found with that ID, cancelling job"

        user = db.User.find_one({ 'email' : alert.email })
        if user is None:
            scheduler.cancel(job)
            # Delete alert
            for c in alert.conditions:
                c.delete()
            alert.delete()
            app.logger.debug("No User found for this alert. Deleted alert.")
            return "No User found for this alert. Deleted alert."

        data_to_send = alert.check()

        if isinstance(alert.sent, datetime):
            can_send_next = alert.sent + timedelta(minutes=alert.frequency)
        else:
            can_send_next = datetime.fromtimestamp(0)

        # Only send email if the alert is active and we have not sent
        # an email within the requested frequency already.
        if not alert.active:
            app.logger.debug("Alert NOT sent.  Is not active.")
            return "Alert NOT sent.  Is not active."

        elif len(data_to_send) < 1:
            app.logger.debug("Alert NOT sent.  No condition matched.")
            return "Alert NOT sent.  No conditions were met."

        elif datetime.utcnow() < can_send_next:
            app.logger.debug("Alert NOT sent.  Already sent within frequency.")
            return "Alert NOT sent.  Already sent within frequency."

        elif len(data_to_send) != len(alert.conditions):
            app.logger.debug("Alert NOT sent.  Only some conditions were met.")
            return "Alert NOT sent.  Only some conditions were met."

        elif len(data_to_send) == len(alert.conditions):
            # All conditions were met

            # Send email
            send("[GLOS Alerts] Conditions met",
                        app.config.get("MAIL_SENDER"),
                        [alert.email],
                        render_template("conditions_met.txt",
                            alert=alert, data=data_to_send, tz=pytz.timezone(user.timezone)),
                        render_template("conditions_met.html",
                            alert=alert, data=data_to_send, tz=pytz.timezone(user.timezone)))

            alert.sent = datetime.utcnow()
            alert.save()

            return "Alert sent"

        else:
            return "Unknown... this shouldn't happen!"