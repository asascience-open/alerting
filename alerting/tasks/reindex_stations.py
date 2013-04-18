from alerting import app
from alerting.models.station import parse_stations

def reindex():
    with app.app_context():
        parse_stations()
        return True
