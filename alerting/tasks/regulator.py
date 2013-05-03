from bson.objectid import ObjectId
from datetime import timedelta, datetime

from alerting import app, db, scheduler

from alerting.tasks.check_alert import check
from alerting.tasks.reindex_stations import reindex_stations

def regulate():
    with app.app_context():

        # Get function and args of 
        jobs = scheduler.get_jobs()

        # Make sure a station update job is running
        update_jobs = [job for job in jobs if job.func == reindex_stations]
        if len(update_jobs) < 1:
            scheduler.schedule(
                scheduled_time=datetime.now(),  # Time for first execution
                func=reindex_stations,          # Function to be queued
                interval=300,                   # Time before the function is called again, in seconds
                repeat=None,                    # Repeat this number of times (None means repeat forever)
                result_ttl=600                  # How long to keep the results
            )

        # Make sure each alert has an alerting job
        alert_jobs = [unicode(job.args[0]) for job in jobs if job.func == check]

        # Get Alerts that have conditions
        alerts = map(lambda x: unicode(x._id), db.Alert.find({ 'conditions' : { '$not' : { '$size' : 0 } } }))

        # Remove the alerts that already have jobs
        for x in alert_jobs:
            try:
                alerts.remove(x)
            except:
                pass

        # Schedule the ones that do not
        for a in alerts:
            scheduler.schedule(
                scheduled_time=datetime.now(),  # Time for first execution
                func=check,                     # Function to be queued
                args=(a,),                      # Arguments passed into function when executed
                interval=300,                   # Time before the function is called again, in seconds
                repeat=None,                    # Repeat this number of times (None means repeat forever)
                result_ttl=600                  # How long to keep the results    
            )
        
    return "Regulated %s alerts and %s update jobs" % (len(alerts), len(update_jobs))