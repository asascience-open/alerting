from flask import render_template, session, jsonify
from alerting import app, db, scheduler
from alerting.models.alert import Alert


@app.route('/', methods=['GET'])
def index():
    user = session.get('user_email', None)
    alerts = []
    stations = []

    if user:
        alerts = db.Alert.find({ 'email' : user })
        stations = db.Station.find()

    return render_template('index.html', alerts=alerts, stations=stations)

@app.route('/jobs', methods=['GET'])
def jobs():
    return jsonify({ "jobs" : str(scheduler.get_jobs()) })