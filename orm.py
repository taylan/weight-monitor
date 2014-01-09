from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import initialize_config, is_debug
from os import environ

initialize_config()

Base = declarative_base()
engine = create_engine('postgresql://{DBUSER}:{DBPASS}@{DBSERVER}:{DBPORT}/{DBNAME}'.format(**environ),
                       echo=is_debug())

song_chord = Table('song_chord', Base.metadata,
                   Column('song_id', Integer, ForeignKey('song.id'), index=True),
                   Column('chord_id', Integer, ForeignKey('chord.id'), index=True)
)


class Measurement(Base):
    __tablename__ = 'measurement'
    id = Column(Integer(), primary_key=True, nullable=False, autoincrement=True)
    measurement_date = Column(DateTime(), nullable=False, index=True)
    value = Column(Integer(), nullable=False)

    def __str__(self):
        return '{0}: {1:.1f}kg'.format(self.measurement_date.strftime('%Y-%m-%d'), self.value)

    def __repr__(self):
        return '{0}({1})'.format(self.__class__, self.measurement_date.strftime('%Y-%m-%d'))


Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
dbsession = Session()
Base.metadata.create_all(engine)
