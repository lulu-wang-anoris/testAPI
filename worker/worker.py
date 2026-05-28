import os
import json
import logging
import traceback
import boto3
import requests
import psycopg2
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]

DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]

sqs = boto3.client("sqs", region_name=AWS_REGION)
s3 = boto3.client("s3", region_name=AWS_REGION)


def get_db_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def update_job(job_id, status, error_message=None):
    conn = get_db_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                if status == "PROCESSING":
                    cur.execute("""
                        UPDATE app.vendor_download_jobs
                        SET status = %s,
                            started_at = COALESCE(started_at, now()),
                            updated_at = now()
                        WHERE job_id = %s
                    """, (status, job_id))
                elif status in ("SUCCEEDED", "FAILED"):
                    cur.execute("""
                        UPDATE app.vendor_download_jobs
                        SET status = %s,
                            error_message = %s,
                            completed_at = now(),
                            updated_at = now()
                        WHERE job_id = %s
                    """, (status, error_message, job_id))
    finally:
        conn.close()


def process_message(message):
    body = json.loads(message["Body"])

    job_id = body["job_id"]
    vendor_url = body.get("vendor_url") or body.get("url")
    s3_bucket = body["s3_bucket"]
    s3_key = body["s3_key"]

    logger.info(f"[{job_id}] Processing job — vendor_url={vendor_url} s3_key={s3_key}")

    update_job(job_id, "PROCESSING")

    with requests.get(vendor_url, stream=True, timeout=120) as response:
        response.raise_for_status()

        s3.upload_fileobj(
            response.raw,
            s3_bucket,
            s3_key,
            ExtraArgs={
                "ContentType": "text/csv"
            }
        )

    update_job(job_id, "SUCCEEDED")

    sqs.delete_message(
        QueueUrl=SQS_QUEUE_URL,
        ReceiptHandle=message["ReceiptHandle"]
    )

    logger.info(f"[{job_id}] Completed — s3://{s3_bucket}/{s3_key}")


def main():
    resp = sqs.receive_message(
        QueueUrl=SQS_QUEUE_URL,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=10,
        VisibilityTimeout=600,
    )

    messages = resp.get("Messages", [])

    if not messages:
        logger.info("No messages found. Exiting.")
        return

    for message in messages:
        try:
            process_message(message)
        except Exception as e:
            logger.error(f"Worker failed: {repr(e)}", exc_info=True)

            try:
                body = json.loads(message["Body"])
                update_job(body["job_id"], "FAILED", str(e))
            except Exception:
                traceback.print_exc()

            raise


if __name__ == "__main__":
    main()
