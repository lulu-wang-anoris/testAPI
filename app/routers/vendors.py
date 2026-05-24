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

router = APIRouter(tags=["Vendor Dataload"])

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
sqs = boto3.client("sqs", region_name=AWS_REGION)


class VendorDownloadRequest(BaseModel):
    vendor: str
    url: HttpUrl
    datasetId: int
    business_date: str
    output_file_name: str


@router.post("/vendor-download-jobs")
def create_vendor_download_job(req: VendorDownloadRequest):
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
        logger.error(f"[{job_id}] ERROR in /vendor-download-jobs: {repr(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    logger.info(f"[{job_id}] Job queued successfully — s3_key={s3_key}")
    return {
        "job_id": job_id,
        "status": "queued",
        "s3_bucket": s3_bucket,
        "s3_key": s3_key,
    }
