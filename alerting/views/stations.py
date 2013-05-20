from bson.objectid import ObjectId
from bson import json_util
import json
from datetime import datetime, timedelta
import time

from flask import render_template, session, request, Response, url_for
from flask.ext.login import current_user

from alerting import app, db, scheduler
from alerting.utils import jsonify, nocache

from alerting.models.alert import Alert

from alerting.tasks.reindex_stations import reindex_stations

@app.route('/stations', methods=['GET'])
def stations():
    if current_user is None:
    	return jsonify({ "error" : "Must be logged in" })

    stations = db.Station.find()

    return_stations = []

    for s in stations:
        s['coordinates'] = s.coordinates()
        s['most_recent_obs'] = s.most_recent_obs()
        del s['updated']
        del s['created']
        del s['geometry']
        del s['timeseries']
        del s['type']
        
        return_stations.append(s)

    return jsonify({ "stations" : return_stations })


@app.route('/stations/reindex', methods=['GET'])
def reindex():
    if current_user and current_user.email == u"wilcox.kyle@gmail.com":
        jobs = scheduler.get_jobs()

        for job in jobs:
            if job.func == reindex_stations or job.description == "alerting.views.stations.reindex()":
               scheduler.cancel(job)
        
        scheduler.schedule(
            scheduled_time=datetime.now(),  # Time for first execution
            func=reindex_stations,          # Function to be queued
            interval=300,                   # Time before the function is called again, in seconds
            repeat=None,                    # Repeat this number of times (None means repeat forever)
            result_ttl=600                  # How long to keep the results
        )

        return jsonify({"message" : "scheduled"})
    else:
        return jsonify({ "error" : "permission denied" })