import os
import json
import uuid
import logging
import traceback
from datetime import datetime, timezone
import boto3
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from app.routers.db import get_db_conn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Datafeed Download"])

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
sqs = boto3.client("sqs", region_name=AWS_REGION)


class DatafeedDownloadRequest(BaseModel):
    vendor: str
    url: HttpUrl
    datasetId: int
    business_date: str
    output_file_name: str


@router.post("/datafeed-download-jobs")
def create_vendor_download_job(req: DatafeedDownloadRequest):
    job_id = str(uuid.uuid4())
    queue_url = os.environ["SQS_QUEUE_URL"]
    s3_bucket = os.environ["S3_BUCKET"]

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    s3_key = (
        f"{req.vendor}/{req.datasetId}/{req.business_date}/"
        f"{req.output_file_name}_{timestamp}_{job_id[:8]}.csv"
    )

    message = {
        "job_id": job_id,
        "vendor": req.vendor,
        "url": str(req.url),
        "datasetId": req.datasetId,
        "business_date": req.business_date,
        "s3_bucket": s3_bucket,
        "s3_key": s3_key,
    }

    logger.info(f"[{job_id}] Starting vendor download job — vendor={req.vendor} datasetId={req.datasetId} business_date={req.business_date}")

    try:
        logger.info(f"[{job_id}] Stage 1/2: Inserting job record into app.vendor_download_jobs")
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO app.vendor_download_jobs (
                job_id, vendor, dataset_id, business_date,
                vendor_url, s3_bucket, s3_key, status
            )
            VALUES (
                %(job_id)s, %(vendor)s, %(dataset_id)s, %(business_date)s,
                %(vendor_url)s, %(s3_bucket)s, %(s3_key)s, 'QUEUED'
            )
        """, {
            "job_id": job_id,
            "vendor": req.vendor,
            "dataset_id": str(req.datasetId),
            "business_date": req.business_date,
            "vendor_url": str(req.url),
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
        })
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"[{job_id}] Stage 1/2: DB insert successful")

        logger.info(f"[{job_id}] Stage 2/2: Sending message to SQS — s3_key={s3_key}")
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message),
        )
        logger.info(f"[{job_id}] Stage 2/2: SQS message sent successfully")

    except Exception as e:
        logger.error(f"[{job_id}] ERROR in /datafeed-download-jobs: {repr(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    logger.info(f"[{job_id}] Job queued successfully — s3_key={s3_key}")
    return {
        "job_id": job_id,
        "status": "queued",
        "s3_bucket": s3_bucket,
        "s3_key": s3_key,
    }


@router.get("/datafeed-download-jobs/{job_id}")
def get_job_status(job_id: str):
    logger.info(f"[{job_id}] Checking job status")
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT job_id, vendor, dataset_id, business_date,
                   vendor_url, s3_bucket, s3_key, status
            FROM app.vendor_download_jobs
            WHERE job_id = %s
        """, (job_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return {
            "job_id": row[0],
            "vendor": row[1],
            "dataset_id": row[2],
            "business_date": row[3],
            "vendor_url": row[4],
            "s3_bucket": row[5],
            "s3_key": row[6],
            "status": row[7],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{job_id}] ERROR checking job status: {repr(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
