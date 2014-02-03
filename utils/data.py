from config import PERIODS
from orm import dbsession, Measurement
from utils.measurement_data import MeasurementData
from datetime import timedelta, datetime


def _calculate_diffs(measurements):
    for i, m in reversed(list(enumerate(measurements))):
        if i == len(measurements) - 1:
            m.diff = 0.0
        else:
            m.diff = m.value - measurements[i + 1].value


def fill_measurement_data_gaps(ms, p):
    new_ms = []
    ms = list(reversed(ms))
    for i, m in enumerate(ms):
        new_ms.append(m)
        if i+1 != len(ms) and (ms[i+1].measurement_date - m.measurement_date).days > 1:
            dt = m.measurement_date + timedelta(days=1)
            while dt < ms[i+1].measurement_date:
                new_ms.append(Measurement(measurement_date=dt, value=m.value, user_id=m.user_id))
                dt = dt + timedelta(days=1)

    return list(reversed(new_ms))[:p]


def get_measurement_data(period, period_name, user_id):
    p = PERIODS.get(period, 7)
    ms = dbsession.query(Measurement).filter(Measurement.user_id == user_id).order_by(
        Measurement.measurement_date.desc()).limit(p).all()

    now = datetime.now().date()
    if ms and ms[0].measurement_date.date() != now:
        ms.insert(0, Measurement(measurement_date=datetime(now.year, now.month, now.day), value=ms[0].value, user_id=user_id))

    ms = fill_measurement_data_gaps(ms, p)
    _calculate_diffs(ms)
    return MeasurementData(period_name, ms, period)
