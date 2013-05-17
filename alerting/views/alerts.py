from bson.objectid import ObjectId
from bson import json_util
import json
from datetime import datetime, timedelta

from flask import render_template, session, request, Response, url_for
from flask.ext.login import current_user

from alerting import app, db, scheduler
from alerting.utils import jsonify, nocache

from alerting.models.alert import Alert

from alerting.tasks.check_alert import check

@app.route('/alerts', methods=['GET'])
@nocache
def alerts():
    alerts = list(db.Alert.find({ 'email' : current_user.email }))

    for a in alerts:
        a['frequency'] = a.user_friendly_frequency()
        a['buffer'] = a.user_friendly_buffer()
        a['checked'] = a.user_friendly_checked()
        a['sent'] = a.user_friendly_sent()
        a['destroy_url'] = url_for('destroy_alert', alert_id=a['_id'])
        a['edit_url'] = url_for('edit_alert', alert_id=a['_id'])
        a['new_condition_url'] = url_for('new_condition', alert_id=a['_id'])

        for c in a.conditions:
            c['destroy_url'] = url_for('destroy_condition', alert_id=a['_id'], condition_id=c['_id'])
            c['values'] = c.data()
            c['times'] = c.times()
            c['station_id'] = c.station()['_id']

        a.conditions = sorted(a.conditions, key=lambda x: x['station_id'])

    return jsonify({ "alerts" : alerts })

@app.route('/alerts/new', methods=['POST'])
def new_alert():
    alert = db.Alert()
    alert.email = current_user.email
    alert.name = request.form.get("name", "")
    alert.frequency = int(request.form.get("frequency", 60))
    alert.buffer = int(request.form.get("buffer", 60))
    if alert.name == "":
        alert.name = u"Unnamed Alert"

    try:
        alert.save()
    except Exception as e:
        app.logger.warn(e.message)
        return jsonify({ "error" : e.message })

    alert['frequency'] = alert.user_friendly_frequency()
    alert['checked'] = alert.user_friendly_checked()
    alert['buffer'] = alert.user_friendly_buffer()
    alert['sent'] = alert.user_friendly_sent()
    alert['destroy_url'] = url_for('destroy_alert', alert_id=alert['_id'])
    alert['edit_url'] = url_for('edit_alert', alert_id=alert['_id'])
    alert['new_condition_url'] = url_for('new_condition', alert_id=alert['_id'])

    # Schedule job to check and send emails if needed
    scheduler.schedule(
        scheduled_time=datetime.now(),  # Time for first execution
        func=check,                     # Function to be queued
        args=(unicode(alert._id),),     # Arguments passed into function when executed
        interval=300,                   # Time before the function is called again, in seconds
        repeat=None,                    # Repeat this number of times (None means repeat forever)
        result_ttl=600                  # How long to keep the results    
    )

    return jsonify(alert)

@app.route('/alerts/<ObjectId:alert_id>/edit', methods=['POST'])
def edit_alert(alert_id):
    alert = db.Alert.find_one({ '_id' : alert_id, 'email' : current_user.email })
    if alert is not None:
        editable = ["name","frequency","buffer","active"]
        for k,v in request.form.iteritems():
            if k in editable:
                alert[k] = type(db.Alert.get(k))(v)

        alert.save()

        alert['frequency'] = alert.user_friendly_frequency()
        alert['checked'] = alert.user_friendly_checked()
        alert['buffer'] = alert.user_friendly_buffer()
        alert['sent'] = alert.user_friendly_sent()
        alert['destroy_url'] = url_for('destroy_alert', alert_id=alert['_id'])
        alert['edit_url'] = url_for('edit_alert', alert_id=alert['_id'])
        alert['new_condition_url'] = url_for('new_condition', alert_id=alert['_id'])
        return jsonify(alert)

    else:
        return jsonify({"message" : "error"})

@app.route('/alerts/<ObjectId:alert_id>/destroy', methods=['POST'])
def destroy_alert(alert_id):
    alert = db.Alert.find_one({ '_id' : alert_id, 'email' : current_user.email })
    if alert is not None:
        for c in alert.conditions:
            try:
                db.Condition.find_one({ '_id' : c['_id'] }).delete()
            except:
                pass
        alert.delete()
        return jsonify({"message" : "success"})
    else:
        return jsonify({"message" : "error"})

@app.route('/alerts/<ObjectId:alert_id>/conditions/new', methods=['POST'])
def new_condition(alert_id):

    alert = db.Alert.find_one({ '_id' : alert_id, 'email' : current_user.email })
    if alert is None:
        return jsonify({"message" : "No alert found with that ID"})
    else:
        c = db.Condition()
        try:
            c.value = float(request.form.get("value"))
        except ValueError:
            return jsonify({ "error" : "Must enter a number as the value" })
        c.variable = request.form.get("variable")
        c.units = request.form.get("units")
        c.comparator = request.form.get("comparator")
        c.station_id = ObjectId(request.form.get("station"))
        try:
            c.save()
        except:
            return jsonify({ "error" : "Error saving conditon, please check inputs" })

        alert.conditions.append(c)
        alert.save()

        c['destroy_url'] = url_for('destroy_condition', alert_id=alert['_id'], condition_id=c['_id'])
        c['values'] = c.data()
        c['times'] = c.times()
        c['station_id'] = c.station()['_id']

        del c['updated']
        
        return jsonify(c)

@app.route('/alerts/<ObjectId:alert_id>/conditions/<ObjectId:condition_id>/destroy', methods=['POST'])
def destroy_condition(alert_id, condition_id):

    alert = db.Alert.find_one({ '_id' : alert_id, 'email' : current_user.email })
    if alert is None:
        return jsonify({"message" : "No alert found with that ID"})
    else:
        condition_to_remove = None
        for c in alert.conditions:
            if c['_id'] == condition_id:
                condition_to_remove = c
                break

        if condition_to_remove is not None:
            try:
                db.Condition.find_one({ '_id' : condition_to_remove['_id'] }).delete()
            except:
                pass
            alert.conditions.remove(condition_to_remove)
            alert.save()
            return jsonify({"message" : "success"})

        return jsonify({"message" : "No condition found with that ID"})

@app.route('/clear')
def clear():
    if current_user and current_user.email == u"wilcox.kyle@gmail.com":
        db.drop_collection('alerts')
        db.drop_collection('conditions')
        return jsonify({ "message" : "ok" })
    else:
        return jsonify({ "error" : "permission denied" })