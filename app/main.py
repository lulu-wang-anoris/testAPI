import os
import psycopg2
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()


def get_db_conn():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
    )

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


@app.get("/db-health")
def db_health():
    try:
        conn = get_db_conn()
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})


@app.get("/db-tables")
def list_tables():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'app' ORDER BY table_name
        """)
        tables = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return {"tables": tables}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})
