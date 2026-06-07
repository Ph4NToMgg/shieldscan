# ShieldScan — Website Security Analyzer

AI-powered website security scanner that checks SSL certificates, HTTP security headers, and HTTPS redirects — with plain-language explanations powered by Google Gemini.

## Tech Stack

| Layer    | Technology                        |
|----------|-----------------------------------|
| Backend  | Python 3.11 + FastAPI             |
| Frontend | React 18 + TypeScript + Vite      |
| Database | PostgreSQL (async via SQLAlchemy)  |
| AI       | Google Gemini 2.5 Flash           |
| Styling  | Tailwind CSS 3                    |

## Project Structure

```
shieldscan/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Environment settings
│   │   ├── database.py          # PostgreSQL async connection
│   │   ├── models/scan.py       # ScanResult DB model
│   │   ├── routers/scan.py      # POST /scan, GET /scan/{id}
│   │   ├── scanners/
│   │   │   ├── ssl_checker.py   # SSL certificate validation
│   │   │   ├── headers_checker.py  # Security headers check
│   │   │   ├── redirect_checker.py # HTTP→HTTPS redirect check
│   │   │   └── orchestrator.py  # Runs all scanners concurrently
│   │   └── ai/explainer.py      # Gemini API integration
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Router setup
│   │   ├── pages/               # HomePage, ResultPage
│   │   ├── components/          # ScanForm, ScoreCard, CheckItem
│   │   └── api/client.ts        # Axios API client
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 14+**
- **Google Gemini API Key** ([Get one here](https://aistudio.google.com/app/apikey))

## Setup

### 1. Database

Create a PostgreSQL database:

```sql
CREATE DATABASE shieldscan;
```

### 2. Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL and GEMINI_API_KEY
```

### 3. Frontend

```bash
cd frontend

# Install dependencies
npm install
```

## Environment Variables

Create a `backend/.env` file with:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/shieldscan
GEMINI_API_KEY=your-gemini-api-key
ALLOWED_ORIGINS=http://localhost:5173
```

| Variable         | Description                                | Required |
|------------------|--------------------------------------------|----------|
| `DATABASE_URL`   | PostgreSQL async connection string         | Yes      |
| `GEMINI_API_KEY` | Google Gemini API key for AI summaries     | Yes      |
| `ALLOWED_ORIGINS`| Comma-separated CORS origins               | No       |

## Running

### Backend (API Server)

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Check health at `http://localhost:8000/health`.

### Frontend (Dev Server)

```bash
cd frontend
npm run dev
```

The app will be available at `http://localhost:5173`. API requests are proxied to the backend automatically.

## API Endpoints

| Method | Endpoint       | Description                      |
|--------|----------------|----------------------------------|
| GET    | `/health`      | Health check                     |
| POST   | `/scan`        | Submit a URL for scanning        |
| GET    | `/scan/{id}`   | Retrieve scan result by ID       |

### Example: Submit a Scan

```bash
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## Security Checks

| Check              | Points | Description                                         |
|--------------------|--------|-----------------------------------------------------|
| SSL Certificate    | 30     | Validates cert, checks expiry (warns <30 days)      |
| Security Headers   | 50     | CSP, X-Frame-Options, X-Content-Type-Options, HSTS, Referrer-Policy (10 pts each) |
| HTTPS Redirect     | 20     | Verifies HTTP→HTTPS redirect is configured          |

## License

MIT
