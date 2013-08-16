import json
import urllib2
from datetime import datetime

from shapely.geometry import Point

from alerting import app, db


def reindex_stations():
    with app.app_context():
        url = "http://data.glos.us/portal/cachedObs.json"
        j = json.loads(urllib2.urlopen(url).read())
        for s in j:
            properties = s.get('properties')
            provider = properties.get('provider')
            description = properties.get('descr')
            station = db.Station.find_one( { 'provider' : provider, 'description' : description })
            if station is None:
                station = db.Station()
                station.provider = provider
                station.description = description

            station.latitude = float(properties.get("lat"))
            station.longitude = float(properties.get("lon"))
            station.geometry = unicode(Point(station.longitude, station.latitude).wkt)
            station.timeseries = properties.get("timeSeries")
            station.link = properties.get("url")
            station.type = properties.get("siteType")
            station.updated = datetime.utcnow()

            station.save()

        return "Stations updated"
