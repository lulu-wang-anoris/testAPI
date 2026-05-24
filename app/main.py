import os
import psycopg2
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pydantic import BaseModel, HttpUrl
import boto3
import json
import uuid
import os

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

# Health check endpoint
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


# PostgreSQL 
@app.get("/db-health", tags=["PostgreSQL"])
def db_health():
    try:
        conn = get_db_conn()
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})


@app.get("/db-tables", tags=["PostgreSQL"])
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

# Vendor data 
sqs = boto3.client("sqs", region_name="us-east-1")

QUEUE_URL = os.environ["SQS_QUEUE_URL"]

S3_BUCKET = os.environ["S3_BUCKET"]

class VendorDownloadRequest(BaseModel):
    vendor: str
    url: HttpUrl
    datasetId: str
    business_date: str

@app.post("/vendor-download-jobs")
def create_vendor_download_job(req: VendorDownloadRequest):

    job_id = str(uuid.uuid4())

    s3_key = (
        f"raw/vendor={req.vendor}/"
        f"dataset={req.dataset}/"
        f"business_date={req.business_date}/"
        f"{job_id}.dat"
    )

    message = {
        "job_id": job_id,
        "vendor": req.vendor,
        "url": str(req.url),
        "dataset": req.dataset,
        "business_date": req.business_date,
        "s3_bucket": S3_BUCKET,
        "s3_key": s3_key
    }

    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(message)
    )
    return {

        "job_id": job_id,
        "status": "queued",
        "s3_key": s3_key

    }