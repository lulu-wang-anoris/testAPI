import os
import json
import uuid
import traceback
import boto3
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl

router = APIRouter(tags=["Vendor Dataload"])

sqs = boto3.client("sqs", region_name="us-east-1")


class VendorDownloadRequest(BaseModel):
    vendor: str
    url: HttpUrl
    datasetId: int
    business_date: str


@router.post("/vendor-download-jobs")
def create_vendor_download_job(req: VendorDownloadRequest):
    job_id = str(uuid.uuid4())
    queue_url = os.environ["SQS_QUEUE_URL"]
    s3_bucket = os.environ["S3_BUCKET"]

    s3_key = (
        f"raw/vendor={req.vendor}/"
        f"dataset={req.datasetId}/"
        f"business_date={req.business_date}/"
        f"{job_id}.dat"
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

    try:
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message),
        )
    except Exception as e:
        print("ERROR in /vendor-download-jobs:", repr(e), flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "job_id": job_id,
        "status": "queued",
        "s3_key": s3_key,
    }
