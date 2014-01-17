class MeasurementData(object):
    def __init__(self, title, data):
        self._title = title
        self._data = data

    @property
    def title(self):
        return self._title

    @property
    def data(self):
        return self._data

    @property
    def total_diff(self):
        return self._data[0].value - self._data[-1].value