# CLAUDE.md

## Project Overview

Lightweight FastAPI REST API deployed to AWS Lightsail via Docker. Connects to a PostgreSQL RDS instance and uses AWS SQS/S3 for vendor data download jobs.

## Project Structure

```
testAPI/
├── app/
│   ├── main.py              # Core endpoints: /, /health, /version, /env
│   └── routers/
│       ├── db.py            # PostgreSQL endpoints: /db-health, /db-tables
│       └── vendors.py       # Vendor endpoints: /vendor-download-jobs
├── .github/
│   └── workflows/
│       └── ci.yml           # Manual deploy pipeline (workflow_dispatch only)
├── Dockerfile               # Container config, exposes port 8080
├── requirements.txt         # Python dependencies
├── .env                     # Local credentials (gitignored, never commit)
├── .env.example             # Credential template (safe to commit)
└── .gitignore
```

## Key Conventions

- Core/general endpoints go in `app/main.py`
- Group new endpoints by domain in `app/routers/` with an `APIRouter`
- DB connections use `get_db_conn()` in `routers/db.py` — don't duplicate connection logic
- Credentials are always read from environment variables via `os.environ`
- Port is `8080` (both Docker and uvicorn)
- Never hardcode credentials or commit `.env`
- Deployment is manual — push to `main` does not auto-deploy

## Adding a New Router

1. Create `app/routers/your_domain.py`:
```python
from fastapi import APIRouter
router = APIRouter(tags=["Your Domain"])

@router.get("/your-endpoint")
def your_endpoint():
    return {"key": "value"}
```

2. Register it in `app/main.py`:
```python
from app.routers import your_domain
app.include_router(your_domain.router)
```

## Adding a DB Endpoint

Use `get_db_conn()` from `routers/db.py` and always close the connection:
```python
@router.get("/my-db-endpoint")
def my_db_endpoint():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT ...")
        result = cur.fetchall()
        cur.close()
        conn.close()
        return {"data": result}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})
```

## Environment Variables

| Variable | Used In | Description |
|----------|---------|-------------|
| `DB_HOST` | `routers/db.py` | RDS endpoint |
| `DB_PORT` | `routers/db.py` | RDS port |
| `DB_NAME` | `routers/db.py` | Database name |
| `DB_USER` | `routers/db.py` | Database user |
| `DB_PASSWORD` | `routers/db.py` | Database password |
| `S3_BUCKET` | `routers/vendors.py` | S3 bucket for vendor data |
| `SQS_QUEUE_URL` | `routers/vendors.py` | SQS queue for download jobs |

## Local Development

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # fill in real credentials
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Deployment

Go to **Actions → Deploy to Lightsail → Run workflow** on GitHub. All env vars are injected from GitHub Secrets — make sure all secrets are set before deploying.
