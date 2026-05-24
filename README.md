# testAPI

A lightweight Python REST API built with FastAPI, containerized with Docker, and deployed to AWS Lightsail.

## Endpoints

### General
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/health` | App health check |
| GET | `/version` | App version |
| GET | `/env` | Safe environment variables |

### PostgreSQL
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/db-health` | PostgreSQL connection check |
| GET | `/db-tables` | List all tables in the `app` schema |

### Vendors
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/vendor-download-jobs` | Queue a vendor data download job to SQS |

## Run Locally

1. Clone the repo:
```bash
git clone git@github-anoris:lulu-wang-anoris/testAPI.git
cd testAPI
```

2. Create a virtual environment and install dependencies:
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

4. Start the server:
```bash
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
```

API will be available at `http://localhost:8080`. Interactive docs at `http://localhost:8080/docs`.

## Run with Docker

```bash
docker build -t testapi .
docker run -p 8080:8080 --env-file .env testapi
```

## Deployment

Deployment is **manual** — pushes to `main` do not auto-deploy. To deploy:

1. Go to **Actions → Deploy to Lightsail → Run workflow**

The workflow will:
1. Build the Docker image
2. Push it to AWS Lightsail
3. Create a new container deployment

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `DB_HOST` | RDS endpoint |
| `DB_PORT` | RDS port (default: 5432) |
| `DB_NAME` | Database name |
| `DB_USER` | Database user |
| `DB_PASSWORD` | Database password |
| `S3_BUCKET` | S3 bucket for vendor data |
| `SQS_QUEUE_URL` | SQS queue URL for vendor download jobs |
