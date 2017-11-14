from datetime import datetime

FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

class NestDate(object):
    """
    wraps basic DateTime objects, but encodes the string
    format we use with the Nest frontend
    format is like: 2012-04-23T18:25:43.511Z
    based on this advice: https://stackoverflow.com/a/15952652/270001
    """

    def __init__(self, datetime_obj):
        self.dt = datetime_obj
        return

    def to_jdata(self):
        s = self.dt.strftime(FORMAT)
        return s

    @staticmethod
    def from_jdata(date_str):
        """
        eg. 2012-04-23T18:25:43.511Z
        """
        dt = datetime.strptime(date_str, FORMAT)
        nest_date = NestDate(dt)
        return nest_date

    @staticmethod
    def now():
        dt = datetime.now()
        nest_date = NestDate(dt)
        return nest_date
