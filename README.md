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

- Frontend: http://127.0.0.1:5173 (or `CDSW_APP_PORT` on CML/CDSW)  
- Backend API: http://127.0.0.1:8000 (or `CDSW_READONLY_PORT` on CML/CDSW)  
- Swagger: http://127.0.0.1:{backend port}/docs  

On Cloudera Machine Learning / CDSW, the platform sets:
- `CDSW_APP_PORT` → Vite frontend on `127.0.0.1`
- API traffic uses internal port **8000** between Vite and FastAPI (loopback-safe)

`CDSW_READONLY_PORT` is not used for in-container proxying — it can cause `EADDRNOTAVAIL` when Vite tries to reach `127.0.0.1:CDSW_READONLY_PORT`. Use the app URL for the UI; `/api` and `/docs` are proxied through Vite. For backend-only on CML, the API binds to `CDSW_READONLY_PORT`.

Options:

```bash
python start.py --skip-install   # skip pip/npm install (faster restarts)
```

Requires **Python 3.10+** and **Node.js/npm**.

### How start.py works

The script is intentionally linear — four steps, no hidden magic:

1. **Install** — `pip install` into `backend/venv`, `npm install` if `node_modules` is missing  
2. **Backend** — FastAPI on `127.0.0.1:8000`  
3. **Wait** — polls `/api/health` until the API is up  
4. **Frontend** — Vite on `127.0.0.1:CDSW_APP_PORT` (or `5173` locally); proxies `/api` to port 8000  

On Cloudera AI, only `CDSW_APP_PORT` matters for the public URL. The API always stays on internal port **8000**.

## Deploying on Cloudera AI (CAI)

### Architecture on CAI

```
Browser  -->  CAI App URL (*.cloudera.site)
                    |
                    v
         Vite @ 127.0.0.1:CDSW_APP_PORT
              |              |
              | /api,/docs   |
              v              v
         FastAPI @ 127.0.0.1:8000  -->  AWS Bedrock
```

The platform exposes only `CDSW_APP_PORT`. The FastAPI backend runs on an internal loopback port; Vite proxies `/api`, `/docs`, and `/openapi.json` to it.

### 1. Project setup (Workbench session)

Use a **Python 3** runtime that includes **Node.js/npm** (required for the React frontend).

```bash
pip install -r requirements.txt
```

Set AWS credentials as **project or application environment variables** (never commit them):

| Variable | Description |
|----------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS access key (or use instance/IAM role) |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_REGION` | e.g. `us-east-1` |

### 2. Create the Application

In Cloudera AI → **Applications** → **New Application**:

| Field | Value |
|-------|-------|
| **Script** | `entry.py` (or `start.py`) |
| **Kernel** | Python 3 |

`entry.py` is a thin wrapper that calls `start.py`. The start script will:

1. Install Python deps into `backend/venv` if needed  
2. Run `npm install` in `frontend/` if needed  
3. Start FastAPI on `127.0.0.1:8000`  
4. Start Vite on `127.0.0.1:$CDSW_APP_PORT`  
5. Wait for the backend health check before opening the frontend  

### 3. Access

- **UI**: open the Application URL from the CAI dashboard  
- **Swagger**: `{app-url}/docs` (proxied through Vite)  
- **Health**: `{app-url}/api/health`  

### CAI environment variables (set by platform)

| Variable | Used for |
|----------|----------|
| `CDSW_APP_PORT` | Vite frontend bind port |
| `CDSW_DOMAIN` | Added to Vite `allowedHosts` |
| `CDSW_READONLY_PORT` | Not used when both services run (see note below) |

`start.py` sets `BACKEND_PROXY_TARGET=http://127.0.0.1:8000` for Vite so the frontend and backend connect correctly inside the workload.

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
