from flask import render_template, session, jsonify

from alerting import app, db

from alerting.models.alert import Alert
from alerting.models.station import parse_stations


@app.route('/', methods=['GET'])
def index():
    user = session.get('user_email', None)
    alerts = []
    stations = []

    if user:
        alerts = db.Alert.find({ 'email' : user })
        stations = db.Station.find()

    return render_template('index.html', alerts=alerts, stations=stations)


@app.route('/reindex', methods=['GET'])
def reindex():
    parse_stations()
    return jsonify({"message" : "success"})