from sqlalchemy import create_engine, Column, DateTime, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import initialize_config, is_debug
from os import environ

initialize_config()

Base = declarative_base()
engine = create_engine('postgresql://{DBUSER}:{DBPASS}@{DBSERVER}:{DBPORT}/{DBNAME}'.format(**environ),
                       echo=is_debug())


class Measurement(Base):
    __tablename__ = 'measurement'
    id = Column(Integer(), primary_key=True, nullable=False, autoincrement=True)
    measurement_date = Column(DateTime(), nullable=False, index=True)
    value = Column(Float(), nullable=False)

    def __str__(self):
        return '{0}: {1:.1f}kg'.format(self.measurement_date.strftime('%Y-%m-%d'), self.value)

    def __repr__(self):
        return '{0}({1})'.format(self.__class__, self.measurement_date.strftime('%Y-%m-%d'))


Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
dbsession = Session()
Base.metadata.create_all(engine)

if is_debug() and dbsession.query(Measurement).count() == 0:
    from json import loads
    from datetime import datetime
    from operator import itemgetter

    wd = []
    with open('weight-data/myfitnesspal-weight-data.json') as mfp_file:
        mfp_data = loads(mfp_file.read())
        [wd.append({'total': x['total'], 'date': datetime.strptime('2013-{0}-{1}'.format(x['date'].split('/')[0], x['date'].split('/')[1]), '%Y-%m-%d')}) for x in mfp_data['data'] if x['total'] != 0]

    with open('weight-data/weightbot_data.csv') as wb_file:
        wb_data = wb_file.read().splitlines()
        [wd.append({'total': float(x.split(',')[1].strip()), 'date': datetime.strptime(x.split(',')[0], '%Y-%m-%d')}) for x in wb_data]

    for d in sorted(wd, key=itemgetter('date')):
        dbsession.add(Measurement(measurement_date=d['date'], value=d['total']))
    dbsession.commit()
