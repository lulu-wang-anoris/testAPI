import boto3
import json
import requests


def get_moodys_credentials():
    client = boto3.client("secretsmanager", region_name="us-east-1")

    response = client.get_secret_value(
        SecretId="anoris/dev/moodys"
    )

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
