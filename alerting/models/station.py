from datetime import datetime

from flask.ext.mongokit import Document

from alerting import db, app

from shapely.wkt import loads
from shapely.geometry import Point

class Station(Document):
    __collection__ = 'stations'
    use_schemaless = True
    use_dot_notation = True
    structure = {
        'description'       : unicode,
        'latitude'          : float,
        'longitude'         : float,
        'geometry'          : unicode, # WKT of the feature
        'timeseries'        : dict, # Data for the station
        'link'              : unicode, # External link to station metadata page
        'type'              : unicode,
        'provider'          : unicode, # Provider of the station (USGS, NDBC, etc.)
        'created'           : datetime,
        'updated'           : datetime
    }
    required_fields = ['latitude', 'longitude', 'geometry','timeseries','provider','created', 'updated']
    default_values = { 'created': datetime.utcnow, 'updated': datetime.utcnow }

    data_fill_values = ["-999999", -999999, "", None, False]
    time_fill_values = ["-999999", -999999, "", None, False]
    ignore_variables = ["MaxWindSpeedTime"]

    def most_recent_obs(self):
        recent = {}
        for var,units in self.variables().items():

            recent[var] = {
                            'time'   : None,
                            'values' : {}
                          }

            for u in units:
                times_and_data = self.times_and_data(variable=var, units=u)

                if len(times_and_data) > 0:
                    recent[var]['time'] = times_and_data[-1][0]
                    recent[var]['values'][u] = times_and_data[-1][1]
                else:
                    recent[var]['values'][u] = []

        return recent

    def variables(self):
        variables = {}

        if self.timeseries:
            for k,v in self.timeseries.items():
                if not isinstance(self.timeseries[k], list):
                    units = self.timeseries[k][u'v'].keys()
                    variables[k] = units

        return variables

    def times_and_data(self, variable=None, units=None):
        d = []
        try:
            if variable not in Station.ignore_variables:
                d = [(datetime.fromtimestamp(t), float(d)) for t,d in zip(self.timeseries[variable][u't'], self.timeseries[variable][u'v'][units]) if d not in Station.data_fill_values and t not in Station.time_fill_values]
        except:
            pass
        # Sort by time
        return sorted(d, key=lambda x: x[0])

    def coordinates(self):
        try:
            geo = loads(self.geometry)
            if isinstance(geo, Point):
                return (geo.coords[0][1], geo.coords[0][0])
            else:
                raise ValueError("Not a point")
        except:
            return None

db.register([Station])

