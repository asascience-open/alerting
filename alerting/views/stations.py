from bson.objectid import ObjectId
from bson import json_util
import json

from flask import render_template, session, request, Response, url_for

from alerting import app, db
from alerting.utils import jsonify

from alerting.models.alert import Alert

@app.route('/stations', methods=['GET'])
def stations():
    user = session.get('user_email', None)
    if user is None:
    	return jsonify({ "error" : "Must be logged in" })

    stations = db.Station.find()

    return_stations = []

    for s in stations:
    	s['variables'] = s.variables()
        s['coordinates'] = s.coordinates()
        del s['updated']
        del s['created']
        del s['geometry']
        del s['timeseries']
        del s['type']
        
        return_stations.append(s)

    return jsonify({ "stations" : return_stations })