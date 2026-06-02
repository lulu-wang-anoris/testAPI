import os
from fastapi import FastAPI
from dotenv import load_dotenv
from app.routers import db, vendors, moodys

load_dotenv()

APP_VERSION = "1.0.0"

app = FastAPI(title="Anoris Capital API", version=APP_VERSION)

app.include_router(db.router)
app.include_router(vendors.router)
app.include_router(moodys.router)


@app.get("/")
def root():
    return {"message": "Welcome to Anoris Capital API system"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": APP_VERSION}


@app.get("/env")
def env():
    safe_keys = {"APP_ENV", "APP_NAME", "PORT", "LOG_LEVEL"}
    return {k: os.environ.get(k, "") for k in safe_keys}
