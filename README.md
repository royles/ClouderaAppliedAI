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

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # Add your AWS credentials
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

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
