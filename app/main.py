from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine, Column, String, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from celery import Celery
import redis
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os

# Database setup
DATABASE_URL = "postgresql://user:password@localhost/dbname"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis & Celery setup
REDIS_URL = "redis://localhost:6379/0"
celery = Celery(__name__, broker=REDIS_URL, backend=REDIS_URL)

# Authentication setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Model for storing metadata
class Metadata(Base):
    __tablename__ = "metadata"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(String)
    keywords = Column(String)
    processed = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Scraper function
def scrape_url(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string if soup.title else ""
        description = soup.find("meta", attrs={"name": "description"})
        keywords = soup.find("meta", attrs={"name": "keywords"})
        return {
            "title": title,
            "description": description["content"] if description else "",
            "keywords": keywords["content"] if keywords else ""
        }
    except Exception as e:
        return None

# Celery task
@celery.task
def process_urls_task(file_path):
    db = SessionLocal()
    df = pd.read_csv(file_path)
    for url in df["URL"]:
        metadata = scrape_url(url)
        if metadata:
            db.add(Metadata(url=url, title=metadata["title"],
                            description=metadata["description"],
                            keywords=metadata["keywords"],
                            processed=True))
    db.commit()
    db.close()
    os.remove(file_path)
    return "Processing completed"

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_location = f"/tmp/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    task = process_urls_task.delay(file_location)
    return {"task_id": task.id}

@app.get("/status/{task_id}")
def get_status(task_id: str):
    task = celery.AsyncResult(task_id)
    return {"task_id": task_id, "status": task.state}

@app.get("/results/{id}")
def get_results(id: int, db: Session = Depends(get_db)):
    result = db.query(Metadata).filter(Metadata.id == id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Not Found")
    return result
