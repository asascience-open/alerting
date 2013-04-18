from bson.objectid import ObjectId
from bson import json_util
import json
from datetime import datetime, timedelta

from flask import render_template, session, request, Response, url_for

from alerting import app, db, scheduler
from alerting.utils import jsonify, nocache

from alerting.models.alert import Alert

from alerting.tasks.check_alert import check

@app.route('/alerts', methods=['GET'])
@nocache
def alerts():
    user = session.get('user_email', None)
    alerts = list(db.Alert.find({ 'email' : user }))

    for a in alerts:
        a['frequency'] = a.user_friendly_frequency()
        a['checked'] = a.user_friendly_checked()
        a['sent'] = a.user_friendly_sent()
        a['destroy_url'] = url_for('destroy_alert', alert_id=a['_id'])
        a['new_condition_url'] = url_for('new_condition', alert_id=a['_id'])

        for c in a.conditions:
            c['destroy_url'] = url_for('destroy_condition', alert_id=a['_id'], condition_id=c['_id'])
            c['timeseries'] = c.data()
            c['station_id'] = c.station()['_id']

        a.conditions = sorted(a.conditions, key=lambda x: x['station_id'])

    return jsonify({ "alerts" : alerts })

@app.route('/alerts/new', methods=['POST'])
def new_alert():
    user = session.get('user_email', None)

    alert = db.Alert()
    alert.email = user
    alert.name = request.form.get("name", "")
    alert.frequency = int(request.form.get("frequency", 60))
    if alert.name == "":
        alert.name = u"Unnamed Alert"

    try:
        alert.save()
    except Exception as e:
        app.logger.warn(e.message)
        return jsonify({ "error" : e.message })

    alert['frequency'] = alert.user_friendly_frequency()
    alert['checked'] = alert.user_friendly_checked()
    alert['sent'] = alert.user_friendly_sent()
    alert['destroy_url'] = url_for('destroy_alert', alert_id=alert['_id'])
    alert['new_condition_url'] = url_for('new_condition', alert_id=alert['_id'])

    # Schedule job to check and send emails if needed
    scheduler.schedule(
        scheduled_time=datetime.now(),  # Time for first execution
        func=check,                     # Function to be queued
        args=(unicode(alert._id),),     # Arguments passed into function when executed
        interval=60,                    # Time before the function is called again, in seconds
        repeat=None,                    # Repeat this number of times (None means repeat forever)
        result_ttl=120                  # How long to keep the results    
    )

    return jsonify(alert)

@app.route('/alerts/<ObjectId:alert_id>/destroy', methods=['POST'])
def destroy_alert(alert_id):
    user = session.get('user_email', None)

    alert = db.Alert.find_one({ '_id' : alert_id, 'email' : user })
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
    user = session.get('user_email', None)

    alert = db.Alert.find_one({ '_id' : alert_id, 'email' : user })
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
        c['timeseries'] = c.data()
        c['station_id'] = c.station()['_id']

        del c['updated']
        
        return jsonify(c)

@app.route('/alerts/<ObjectId:alert_id>/conditions/<ObjectId:condition_id>/destroy', methods=['POST'])
def destroy_condition(alert_id, condition_id):
    user = session.get('user_email', None)

    alert = db.Alert.find_one({ '_id' : alert_id, 'email' : user })
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
    user = session.get('user_email', None)
    if user == "wilcox.kyle@gmail.com":
        db.drop_collection('alerts')
        db.drop_collection('conditions')
        return jsonify({ "message" : "ok" })
    else:
        return jsonify({ "error" : "permission denied" })