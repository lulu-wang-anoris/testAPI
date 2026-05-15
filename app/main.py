import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

APP_VERSION = "1.0.0"


app = FastAPI(title="TestAPI", version=APP_VERSION)


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
