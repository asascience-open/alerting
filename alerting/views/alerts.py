from bson.objectid import ObjectId
from bson import json_util
import json

from flask import render_template, session, request, Response, url_for

from alerting import app, db
from alerting.utils import jsonify

from alerting.models.alert import Alert

@app.route('/alerts', methods=['GET'])
def alerts():
    user = session.get('user_email', None)
    alerts = db.Alert.find({ 'email' : user })[:]

    new_alerts = []

    for a in alerts:
        station = json.loads(json.dumps(db.Station.find_one( { '_id' : a.station_id } ), default=json_util.default))
        del station['updated']
        del station['created']
        del station['_id']
        del station['last_obs']
        del station['type']
        a['station'] = station
        a['destroy_url'] = url_for('destroy_alert', alert_id=a['_id'])
        a['new_condition_url'] = url_for('new_condition', alert_id=a['_id'])

        for c in a.conditions:
            c['destroy_url'] = url_for('destroy_condition', alert_id=a['_id'], condition_id=c['_id'])

        new_alerts.append(a)

    return jsonify({ "alerts" : new_alerts })

@app.route('/alerts/new', methods=['POST'])
def new_alert():
    user = session.get('user_email', None)

    alert = db.Alert()
    alert.email = user
    alert.name = request.form.get("name", "Alert")
    alert.station_id = ObjectId(request.form.get("station_id"))
    try:
        alert.save()
    except Exception as e:
        alert = { "error" : e.message }

    station = json.loads(json.dumps(db.Station.find_one( { '_id' : alert.station_id } ), default=json_util.default))
    del station['updated']
    del station['created']
    del station['_id']
    del station['last_obs']
    del station['type']
    alert['station'] = station
    a['destroy_url'] = url_for('destroy_alert', alert_id=a['_id'])
    a['new_condition_url'] = url_for('new_condition', alert_id=a['_id'])

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
        c.comparator = request.form.get("comparator")
        c.save()

        alert.conditions.append(c)
        alert.save()

        c['destroy_url'] = url_for('destroy_condition', alert_id=alert['_id'], condition_id=c['_id'])
        del c['updated']
        del c['_id']
        
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
