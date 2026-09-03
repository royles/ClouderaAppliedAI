# Bedrock Playground

A lightweight playground for experimenting with AWS Bedrock models. The React frontend provides a simple chat UI; the FastAPI backend handles all AWS connectivity and keeps credentials secure.

## Architecture

```
┌─────────────────┐      /api/*       ┌──────────────────┐      boto3       ┌─────────────┐
│  React (Vite)   │ ────────────────► │  FastAPI Backend │ ─────────────► │ AWS Bedrock │
│  localhost:5173 │                   │  localhost:8000  │                │             │
└─────────────────┘                   └──────────────────┘                └─────────────┘
                                              │
                                              ▼
                                    Environment / IAM role
                                    (secrets never in frontend)
```

## Security

- **AWS credentials** are read only by the backend from environment variables or the default IAM credential chain (e.g. EC2/ECS instance role).
- **No secrets** are exposed to the React app or returned by `/api/config`.
- Copy `backend/.env.example` to `backend/.env` for local development — never commit `.env`.
- In production, prefer IAM roles over long-lived access keys.
- CORS is restricted to configured origins (`CORS_ORIGINS`).

## Quick Start

### One command (recommended)

From the repo root, this installs Python and npm dependencies if needed and starts both services:

```bash
cp backend/.env.example backend/.env   # optional: add AWS credentials
python start.py
```

- Frontend: http://127.0.0.1:5173 (or `CDSW_APP_PORT` in Cloudera CML/CDSW)  
- Backend API: http://127.0.0.1:8000  
- Swagger: http://127.0.0.1:8000/docs  

On Cloudera Machine Learning / CDSW, the platform sets `CDSW_APP_PORT`; `start.py` uses it automatically for the Vite dev server on `127.0.0.1`.

Options:

```bash
python start.py --backend-only      # API only
python start.py --frontend-only     # UI only (proxies /api to backend if running)
python start.py --skip-install      # skip pip/npm install checks
python start.py --frontend-host 127.0.0.1 --frontend-port 8090
python start.py --backend-port 9000
```

Requires **Python 3.10+** and **Node.js/npm** on your machine.

### Manual setup

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # Add your AWS credentials
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | API and AWS credential status |
| `/api/models` | GET | List available Bedrock models |
| `/api/config` | GET | Current model and region (no secrets) |
| `/api/config` | PUT | Update model or region |
| `/api/chat` | POST | Send chat messages to Bedrock |

### Example: update model

```bash
curl -X PUT http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"model_id": "anthropic.claude-3-haiku-20240307-v1:0"}'
```

### Example: chat

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
```

## Configuration

Environment variables (backend only):

| Variable | Description |
|----------|-------------|
| `AWS_ACCESS_KEY_ID` | Optional — use IAM role if unset |
| `AWS_SECRET_ACCESS_KEY` | Optional |
| `AWS_SESSION_TOKEN` | Optional — for temporary credentials |
| `AWS_REGION` | Default AWS region |
| `DEFAULT_MODEL_ID` | Initial Bedrock model |
| `CORS_ORIGINS` | Allowed frontend origins |

## Supported Models

Anthropic Claude 3/3.5, Amazon Titan, Meta Llama 3, and Mistral models are pre-configured. Add more in `backend/app/models_catalog.py`.
