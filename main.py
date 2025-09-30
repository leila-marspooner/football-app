from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import whisper
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Import your custom parser
from parser import SimpleParser

# Database Setup
Base = declarative_base()

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.now)
    opponent = Column(String(255))

class RawEvent(Base):
    __tablename__ = "raw_events"
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer)
    transcription = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)

class ParsedEvent(Base):
    __tablename__ = "parsed_events"
    id = Column(Integer, primary_key=True)
    raw_event_id = Column(Integer, nullable=False)
    match_id = Column(Integer, nullable=False)
    event_type = Column(String(50))
    player = Column(String(100))
    confidence = Column(String(10))
    raw_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

# Create SQLite database
engine = create_engine('sqlite:///football.db', echo=True)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

# Initialize FastAPI
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Whisper model
print("Loading Whisper model...")
model = whisper.load_model("tiny")
print("Whisper model loaded!")
parser = SimpleParser()

@app.get("/")
def read_root():
    return {"message": "Football Voice Tracker API", "status": "running"}

@app.post("/transcribe/")
async def transcribe(file: UploadFile = File(...), match_id: int = 1):
    temp_file = f"temp_{file.filename}"
    try:
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)

        result = model.transcribe(temp_file)
        transcription = result["text"]

        db = SessionLocal()
        try:
            # Save raw event
            raw_event = RawEvent(
                match_id=match_id,
                transcription=transcription,
                timestamp=datetime.now()
            )
            db.add(raw_event)
            db.commit()
            db.refresh(raw_event)

            # Parse into multiple events
            parsed_events_list = parser.parse(transcription)

            # Save each parsed event
            saved_parsed_ids = []
            for parsed in parsed_events_list:
                parsed_event = ParsedEvent(
                    raw_event_id=raw_event.id,
                    match_id=match_id,
                    event_type=parsed["type"],
                    player=parsed.get("player"),
                    confidence=str(parsed["confidence"]),
                    raw_text=parsed["raw_text"],
                    timestamp=datetime.now()
                )
                db.add(parsed_event)
                db.commit()
                db.refresh(parsed_event)
                saved_parsed_ids.append(parsed_event.id)

            response = {
                "transcription": transcription,
                "parsed_events": parsed_events_list,
                "saved": True,
                "raw_event_id": raw_event.id,
                "parsed_event_ids": saved_parsed_ids,
                "match_id": match_id
            }

        finally:
            db.close()

        if os.path.exists(temp_file):
            os.remove(temp_file)

        return response

    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return {"error": str(e), "saved": False}
@app.get("/events/raw/{match_id}")
async def get_raw_events(match_id: int):
    db = SessionLocal()
    try:
        events = db.query(RawEvent).filter_by(match_id=match_id).order_by(RawEvent.timestamp).all()
        return {
            "match_id": match_id,
            "event_count": len(events),
            "events": [
                {
                    "id": e.id,
                    "transcription": e.transcription,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in events
            ]
        }
    finally:
        db.close()

@app.get("/events/parsed/{match_id}")
async def get_parsed_events(match_id: int):
    db = SessionLocal()
    try:
        events = db.query(ParsedEvent).filter_by(match_id=match_id).order_by(ParsedEvent.timestamp).all()
        return {
            "match_id": match_id,
            "event_count": len(events),
            "events": [
                {
                    "id": e.id,
                    "raw_event_id": e.raw_event_id,
                    "event_type": e.event_type,
                    "player": e.player,
                    "confidence": e.confidence,
                    "raw_text": e.raw_text,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in events
            ]
        }
    finally:
        db.close()

@app.post("/matches/create")
async def create_match(opponent: str = "Unknown Team"):
    db = SessionLocal()
    try:
        match = Match(opponent=opponent, date=datetime.now())
        db.add(match)
        db.commit()
        db.refresh(match)
        return {"match_id": match.id, "opponent": opponent, "created": True}
    finally:
        db.close()

@app.get("/matches/")
async def get_matches():
    db = SessionLocal()
    try:
        matches = db.query(Match).order_by(Match.date.desc()).all()
        return {
            "matches": [
                {
                    "id": m.id,
                    "opponent": m.opponent,
                    "date": m.date.isoformat()
                }
                for m in matches
            ]
        }
    finally:
        db.close()

@app.delete("/events/raw/{event_id}")
async def delete_raw_event(event_id: int):
    db = SessionLocal()
    try:
        raw_event = db.query(RawEvent).filter_by(id=event_id).first()
        if not raw_event:
            return {"deleted": False, "error": "Raw event not found"}

        parsed_event = db.query(ParsedEvent).filter_by(raw_event_id=event_id).first()
        if parsed_event:
            db.delete(parsed_event)

        db.delete(raw_event)
        db.commit()
        return {"deleted": True, "event_id": event_id}
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)