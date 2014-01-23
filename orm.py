from sqlalchemy import create_engine, Column, DateTime, Float, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask.ext.login import UserMixin
from config import initialize_config, is_debug
from os import environ

initialize_config()

Base = declarative_base()
engine = create_engine('postgresql://{DBUSER}:{DBPASS}@{DBSERVER}:{DBPORT}/{DBNAME}'.format(**environ), echo=is_debug())


class User(Base, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer(), primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(), nullable=False)
    email = Column(String(), nullable=False)
    password_hash = Column(String(), nullable=False)
    password_salt = Column(String(), nullable=False)

    def first_name(self):
        return self.name.split(' ')[0]


class Measurement(Base):
    __tablename__ = 'measurement'
    id = Column(Integer(), primary_key=True, nullable=False, autoincrement=True)
    measurement_date = Column(DateTime(), nullable=False, index=True)
    value = Column(Float(), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    def __str__(self):
        return '{0}: {1:.1f}kg'.format(self.measurement_date.strftime('%Y-%m-%d'), self.value)

    def __repr__(self):
        return '{0}({1})'.format(self.__class__, self.measurement_date.strftime('%Y-%m-%d'))


Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
dbsession = Session()
Base.metadata.create_all(engine)

if dbsession.query(Measurement).count() == 0:
    print('Measurement table is empty. Filling with data from Weightbot and MyFitnessPal.')
    me = dbsession.query(User).filter(User.email == 'taylanaydinli@gmail.com').first()
    if not me:
        me = User(email='taylanaydinli@gmail.com', name='Taylan Aydinli', password_hash='x', password_salt='x')
        dbsession.add(me)
        dbsession.commit()

    from operator import itemgetter
    from utils.weightdataloader import get_weight_data

    for d in sorted(get_weight_data(), key=itemgetter('date')):
        dbsession.add(Measurement(measurement_date=d['date'], value=d['total'], user_id=me.id))
    dbsession.commit()
