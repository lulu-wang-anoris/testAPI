import logging
import boto3
import json
import requests
from fastapi import APIRouter, HTTPException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Moodys"])


def get_moodys_credentials():
    client = boto3.client("secretsmanager", region_name="us-east-1")
    response = client.get_secret_value(SecretId="anoris/dev/moodys")
    return json.loads(response["SecretString"])


def get_moodys_dts_token():
    secret = get_moodys_credentials()
    response = requests.get(
        "https://wsasupport.moodysanalytics.com/dts_tokens",
        headers={"Accept": "application/json"},
        auth=(secret["MOODYS_USERNAME"], secret["MOODYS_PASSWORD"]),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


@router.get("/moodys/token-check")
def token_check():
    logger.info("Requesting Moodys DTS token")
    try:
        token = get_moodys_dts_token()
        logger.info("Moodys DTS token retrieved successfully")
        return {
            "status": "ok",
            "token_preview": token[:10] + "...",
        }
    except Exception as e:
        logger.error(f"Failed to retrieve Moodys DTS token: {repr(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
