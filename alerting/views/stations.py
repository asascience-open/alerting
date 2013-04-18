from bson.objectid import ObjectId
from bson import json_util
import json
from datetime import datetime, timedelta
import time

from flask import render_template, session, request, Response, url_for

from alerting import app, db, scheduler
from alerting.utils import jsonify, nocache

from alerting.models.alert import Alert

from alerting.tasks.reindex_stations import reindex

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


@app.route('/stations/reindex', methods=['GET'])
def reindex():
    jobs = scheduler.get_jobs()

    for job in jobs:
        if job.func == reindex:
           scheduler.cancel(job)
    
    scheduler.schedule(
        scheduled_time=datetime.now(),  # Time for first execution
        func=reindex,                   # Function to be queued
        interval=60,                    # Time before the function is called again, in seconds
        repeat=None,                    # Repeat this number of times (None means repeat forever)
        result_ttl=120                  # How long to keep the results    
    )

    return jsonify({"message" : "scheduled"})