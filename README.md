# Digital Footprint & Cybersecurity Audit Platform

This repository contains a FastAPI backend and a React + Tailwind frontend for consent-based digital footprint scans with real-time WebSocket updates.

## Secure Setup

1. Create an environment file in the repository root:

```bash
cp .env.example .env
```

2. Configure required values:

- `HIBP_API_KEY` (required for live HaveIBeenPwned queries)
- `HIBP_USER_AGENT` (optional, defaults to `Email-Search-Audit`)
- `REDIS_URL` (optional, defaults to `redis://redis:6379/0`)

3. Start all services:

```bash
docker compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## Local Development

### Backend

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API

- `POST /api/v1/scan` (rate-limited to `5/minute` per IP)
- `WS /ws/{scan_id}` for streaming scan status updates

## Consent Requirement

Scans are only accepted when `user_consent=true` and strict target validation passes:

- Email: regex validation
- Phone: E.164 format (e.g., `+1234567890`)
