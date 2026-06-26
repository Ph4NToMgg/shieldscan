# 🛡️ ShieldScan — Website Security Analyzer

AI-powered website security scanner that audits SSL certificates, HTTP security headers, HTTPS redirects, cookie security, mixed content, and domain expiry — with plain-language explanations and fix suggestions powered by **Google Gemini 2.5 Flash**.

🔗 **Live Demo:** [shieldscan-nine.vercel.app](https://shieldscan-nine.vercel.app)

---

## ✨ Features

- **6 Security Checks** — SSL, headers (7 types + leakage detection), HTTPS redirect, cookies, mixed content, domain WHOIS
- **AI-Powered Reports** — Google Gemini translates technical findings into plain language with actionable fix suggestions
- **User Authentication** — Email/password registration and login via Supabase Auth
- **Credit System** — 3 free scans on signup; purchasable credit packages (coming soon)
- **Scan History** — View and revisit all past scan results
- **Live Stats** — Real-time total scan counter with keep-alive ping (prevents Render free-tier sleep)
- **Responsive Design** — Premium dark UI that works on desktop and mobile

---

## 🏗️ Tech Stack

| Layer          | Technology                                      |
|----------------|--------------------------------------------------|
| Backend        | Python 3.11 · FastAPI · Uvicorn                  |
| Frontend       | React 18 · TypeScript · Vite                     |
| Database       | PostgreSQL (async via SQLAlchemy + asyncpg)       |
| Authentication | Supabase Auth (JWT/JWKS verification)             |
| AI             | Google Gemini 2.5 Flash                           |
| Styling        | Tailwind CSS + custom design system               |
| Hosting        | Render (backend) · Vercel (frontend) · Supabase (DB + Auth) |

---

## 📁 Project Structure

```
shieldscan/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, lifespan, CORS, global error handler
│   │   ├── config.py               # Environment settings (Pydantic)
│   │   ├── database.py             # PostgreSQL async engine & session
│   │   ├── auth.py                 # JWT verification via Supabase JWKS
│   │   ├── limiter.py              # SlowAPI rate limiter
│   │   ├── models/
│   │   │   ├── scan.py             # ScanResult DB model
│   │   │   └── user_credits.py     # UserCredits DB model
│   │   ├── routers/
│   │   │   └── scan.py             # All scan endpoints (create, history, credits, stats)
│   │   ├── scanners/
│   │   │   ├── ssl_checker.py      # SSL certificate validation
│   │   │   ├── headers_checker.py  # 7 security headers + leakage detection
│   │   │   ├── redirect_checker.py # HTTP → HTTPS redirect check
│   │   │   ├── cookie_checker.py   # Cookie security flags (Secure, HttpOnly, SameSite)
│   │   │   ├── mixed_content_checker.py  # HTTP resources on HTTPS pages
│   │   │   ├── domain_checker.py   # WHOIS domain expiry check
│   │   │   └── orchestrator.py     # Runs all scanners concurrently & scores
│   │   └── ai/
│   │       └── explainer.py        # Google Gemini AI summary generation
│   ├── requirements.txt
│   ├── runtime.txt                 # Python version for Render
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx                 # Router setup
│   │   ├── main.tsx                # React entry point
│   │   ├── index.css               # Full design system (dark theme)
│   │   ├── types.ts                # TypeScript type definitions
│   │   ├── api/
│   │   │   └── client.ts           # Axios client with auth interceptor
│   │   ├── lib/
│   │   │   └── supabase.ts         # Supabase client initialization
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx      # Auth state management (React Context)
│   │   ├── components/
│   │   │   ├── Navbar.tsx           # Top navigation bar with stats & credits
│   │   │   ├── ScanForm.tsx         # URL input form
│   │   │   ├── ScoreCard.tsx        # Animated score display
│   │   │   └── CheckItem.tsx        # Individual check result card
│   │   └── pages/
│   │       ├── HomePage.tsx         # Landing page with scan form
│   │       ├── ResultPage.tsx       # Detailed scan results with AI summary
│   │       ├── LoginPage.tsx        # Login / Register page
│   │       └── HistoryPage.tsx      # Scan history table
│   ├── public/
│   │   └── favicon.svg             # Shield favicon
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

---

## 🔒 Security Checks

All 6 checks run concurrently for maximum speed. The total score is calculated on a weighted 0–100 scale:

| Check                 | Weight | What it does                                                                      |
|-----------------------|--------|-----------------------------------------------------------------------------------|
| **SSL Certificate**   | 20 pts | Validates certificate, checks expiry (warns < 30 days), identifies issuer         |
| **Security Headers**  | 35 pts | Checks 7 headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, X-Permitted-Cross-Domain-Policies) with quality analysis. Detects info leakage via Server/X-Powered-By version disclosure (-3 pts penalty each) |
| **HTTPS Redirect**    | 15 pts | Verifies HTTP → HTTPS redirect (301/302/307/308)                                  |
| **Mixed Content**     | 15 pts | Parses HTML for resources loaded over insecure HTTP on HTTPS pages                 |
| **Cookie Security**   | 10 pts | Checks all cookies for Secure, HttpOnly, and SameSite flags                        |
| **Domain Expiry**     |  5 pts | WHOIS lookup for domain registration expiry date                                   |

---

## ⚙️ Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 14+** (or Supabase)
- **Google Gemini API Key** — [Get one here](https://aistudio.google.com/app/apikey)
- **Supabase Project** — [Create one here](https://supabase.com) (for auth & database)

---

## 🚀 Setup

### 1. Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — see Environment Variables section below
```

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install
```

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

---

## 🔑 Environment Variables

### Backend (`backend/.env`)

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/shieldscan
GEMINI_API_KEY=your-gemini-api-key
SUPABASE_URL=https://your-project.supabase.co
ALLOWED_ORIGINS=http://localhost:5173
```

| Variable          | Description                            | Required |
|-------------------|----------------------------------------|----------|
| `DATABASE_URL`    | PostgreSQL async connection string     | Yes      |
| `GEMINI_API_KEY`  | Google Gemini API key for AI summaries | Yes      |
| `SUPABASE_URL`    | Supabase project URL (for JWKS auth)   | Yes      |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins           | No       |

### Frontend (`frontend/.env`)

| Variable                 | Description                   | Required |
|--------------------------|-------------------------------|----------|
| `VITE_API_URL`           | Backend API base URL          | Yes      |
| `VITE_SUPABASE_URL`      | Supabase project URL          | Yes      |
| `VITE_SUPABASE_ANON_KEY` | Supabase anonymous key        | Yes      |

### Production (Render + Vercel)

On **Render**, set `DATABASE_URL`, `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `ALLOWED_ORIGINS`.

On **Vercel**, set `VITE_API_URL`, `VITE_SUPABASE_URL`, and `VITE_SUPABASE_ANON_KEY`.

---

## ▶️ Running Locally

### Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API available at `http://localhost:8000`. Health check: `http://localhost:8000/health`.

### Frontend

```bash
cd frontend
npm run dev
```

App available at `http://localhost:5173`.

---

## 📡 API Endpoints

| Method | Endpoint              | Auth     | Description                          |
|--------|-----------------------|----------|--------------------------------------|
| GET    | `/health`             | No       | Health check                         |
| POST   | `/scan`               | Required | Submit a URL for security scanning   |
| GET    | `/scan/{id}`          | No       | Retrieve a scan result by ID         |
| GET    | `/scan/history`       | Required | Get authenticated user's scan history|
| GET    | `/scan/credits`       | Required | Get user's credit balance            |
| GET    | `/scan/stats`         | No       | Get total scans performed (global)   |

### Example: Submit a Scan

```bash
curl -X POST https://shieldscan-dnwt.onrender.com/scan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"url": "https://example.com"}'
```

---

## 🎨 Design

ShieldScan uses a custom **"Refined Dark Precision"** design system with:

- Dark base (`#0a0a0a`) with elevated surfaces
- Lime-green accent (`#e8ff00`) for CTAs and highlights
- Monospace typography (JetBrains Mono) for data
- Display font (Instrument Serif) for headings
- Glassmorphism effects with backdrop blur
- Smooth micro-animations and transitions
- Fully responsive layout

---

## 📄 License

MIT
