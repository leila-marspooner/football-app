# database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.now)
    opponent = Column(Text)

class RawEvent(Base):
    __tablename__ = "raw_events"
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer)
    transcription = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)

# Create database
engine = create_engine('sqlite:///football.db')
Base.metadata.create_all(engine)