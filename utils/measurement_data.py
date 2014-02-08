class MeasurementData(object):
    def __init__(self, title, data, period):
        self._title = title
        self._data = data
        self._period = period

    @property
    def title(self):
        return self._title

    @property
    def data(self):
        return self._data

    @property
    def period(self):
        return self._period

    @property
    def has_data(self):
        return True if self._data else False

    @property
    def total_diff(self):
        return self._data[0].value - self._data[-1].value if self._data else 0
