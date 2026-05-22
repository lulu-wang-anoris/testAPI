# CLAUDE.md

## Project Overview

Lightweight FastAPI REST API deployed to AWS Lightsail via Docker. Connects to a PostgreSQL RDS instance on AWS.

## Project Structure

```
testAPI/
├── app/
│   └── main.py          # All endpoints and DB connection logic
├── .github/
│   └── workflows/
│       └── ci.yml       # GitHub Actions deploy pipeline
├── Dockerfile           # Container config, exposes port 8080
├── requirements.txt     # Python dependencies
├── .env                 # Local credentials (gitignored, never commit)
├── .env.example         # Credential template (safe to commit)
└── .gitignore
```

## Key Conventions

- All endpoints live in `app/main.py`
- DB connections use the `get_db_conn()` helper — don't duplicate connection logic
- Credentials are always read from environment variables via `os.environ`
- Port is `8080` (both Docker and uvicorn)
- Never hardcode credentials or commit `.env`

## Adding a New Endpoint

Add it to `app/main.py`:
```python
@app.get("/my-endpoint")
def my_endpoint():
    return {"key": "value"}
```

For DB endpoints, use the `get_db_conn()` helper and always close the connection:
```python
@app.get("/my-db-endpoint")
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

## Local Development

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # fill in real credentials
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Deployment

Push to `main` — GitHub Actions handles the rest. Requires AWS and DB secrets set in GitHub repo settings.
