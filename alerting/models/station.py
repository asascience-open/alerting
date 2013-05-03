from datetime import datetime

from flask.ext.mongokit import Document

from alerting import db, app

from shapely.wkt import loads
from shapely.geometry import Point

import pytz

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
        'last_obs'          : dict, # Simple access to most recent data
        'link'              : unicode, # External link to station metadata page
        'type'              : unicode,
        'provider'          : unicode, # Provider of the station (USGS, NDBC, etc.)
        'created'           : datetime,
        'updated'           : datetime
    }
    required_fields = ['latitude', 'longitude', 'geometry','timeseries','provider','created', 'updated']
    default_values = { 'created': datetime.utcnow, 'updated': datetime.utcnow }

    data_fill_values = ["-999999", -999999]
    time_fill_values = ["-999999", -999999]

    def variables(self):
        variables = {}

        if self.timeseries:
            for k,v in self.timeseries.items():
                if not isinstance(self.timeseries[k], list):
                    units = self.timeseries[k][u'v'].keys()
                    variables[k] = units

        if self.last_obs:
            for k,v in self.last_obs.items():
                if not variables.get(k, None) and not isinstance(self.last_obs[k][u'v'], list):
                    units = self.last_obs[k][u'v'].keys()
                    variables[k] = units

        return variables

    def data(self, variable=None, units=None):
        if self.timeseries and variable is not None and units is not None:
            return [float(x) for x in self.timeseries[variable][u'v'][units] if x not in Station.data_fill_values]
        else:
            return []

    def times(self, variable=None):
        if self.timeseries and variable is not None:
            return [datetime.fromtimestamp(x) for x in self.timeseries[variable][u't'] if x not in Station.time_fill_values]
        else:
            return []

    def times_and_data(self, variable=None, units=None):
        if self.timeseries and variable is not None and units is not None:
            return [(datetime.fromtimestamp(t), float(d)) for t,d in zip(self.timeseries[variable][u't'], self.timeseries[variable][u'v'][units]) if d not in Station.data_fill_values and t not in Station.time_fill_values]
        else:
            return []

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

