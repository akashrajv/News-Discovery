# Multi-Source News Collection Engine

Production-style, modular **Multi-Source News Collection Engine** built for AI-powered News Intelligence Platforms. This engine handles news discovery, connector fetching, field normalization, recency filtering, multi-stage deduplication, sliding-window rate limiting, TTL caching, cost tracking, failure fallback, and persistence.

---

## 1. Project Purpose
This engine forms the **collection layer** of an AI News Intelligence Platform. It provides a reliable, cost-aware pipeline to discover and collect news across permitted API endpoints, public RSS feeds, and structured authorized feeds without depending on a single news API vendor.

> [!NOTE]
> **Scope Boundary**: This layer exclusively handles discovery, collection, normalization, recency filtering, deduplication, caching, rate limiting, and cost tracking. It does NOT perform downstream NLP/LLM tasks (sentiment analysis, event clustering, summarization, or embeddings).

---

## 2. Architecture & Pipeline Data Flow

```
User Monitoring Request (POST /api/collect-news)
       │
       ▼
Source Registry ──► Source Router (Cost & Priority Evaluator)
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
       NewsAPI / GNews   RSS Feeds   Authorized Feeds
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                     Fetch Articles
                           │
                           ▼
                    Normalize Data
                           │
                           ▼
                    Recency Filtering (10m, 30m, 1h, 6h, 24h)
                           │
                           ▼
             Multi-Stage Deduplication Engine
             (Canonical URL, Title, MD5 Hash, Title Similarity)
                           │
                           ▼
               Redis / In-Memory Cache TTL Check
                           │
                           ▼
            Database Persistence (Postgres / SQLite)
                           │
                           ▼
           Return Unified Response ──► React Dashboard
```

---

## 3. Folder Structure

```
news-collection-engine/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI server entrypoint
│   │   ├── config.py                # Environment configuration & fallbacks
│   │   ├── api/                     # REST API Routes
│   │   │   ├── routes_collect.py    # POST /api/collect-news
│   │   │   ├── routes_articles.py   # GET /api/articles, GET /api/articles/{id}
│   │   │   ├── routes_sources.py    # GET /api/sources, GET /api/sources/status, POST
│   │   │   ├── routes_usage.py      # GET /api/usage
│   │   │   ├── routes_history.py    # GET /api/collection-history
│   │   │   ├── routes_health.py     # GET /api/health
│   │   │   ├── routes_cache.py      # GET /api/cache/status
│   │   │   └── routes_routing.py    # GET /api/routing/last-decision
│   │   ├── connectors/              # Pluggable Connectors
│   │   │   ├── base.py              # BaseConnector abstract class
│   │   │   ├── api_connector.py     # Base HTTP REST API connector
│   │   │   ├── rss_connector.py     # RSS/Atom connector (feedparser)
│   │   │   ├── authorized_feed_connector.py # Structured JSON feed connector
│   │   │   ├── newsapi_connector.py # NewsAPI adapter
│   │   │   ├── gnews_connector.py   # GNews adapter
│   │   │   └── newsdata_connector.py # NewsData.io adapter
│   │   ├── router/
│   │   │   └── source_router.py     # Cost-aware router
│   │   ├── registry/
│   │   │   └── source_registry.py   # Dynamic source registry & initializer
│   │   ├── services/                # Business Logic Pipeline Services
│   │   │   ├── collection_service.py   # Main pipeline orchestrator
│   │   │   ├── normalization_service.py# Schema mapping
│   │   │   ├── recency_service.py      # Recency cutoff filter
│   │   │   ├── deduplication_service.py# Multi-stage duplicate detector
│   │   │   ├── cache_service.py        # Redis + In-memory fallback
│   │   │   ├── rate_limit_service.py   # Quota tracker & retry backoff
│   │   │   ├── cost_service.py         # Cost estimator & metrics aggregator
│   │   │   ├── health_service.py       # Engine health monitor
│   │   │   └── demo_service.py         # Deterministic mock data generator
│   │   ├── database/
│   │   │   ├── database.py          # SQLAlchemy engine & SQLite fallback
│   │   │   └── models.py            # ORM Database Models
│   │   ├── schemas/                 # Pydantic Request/Response models
│   │   └── utils/                   # Text normalization, hashing, logging
│   ├── tests/                       # Pytest test suite
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/              # Modular UI components (Form, Stats, Router, Table, Modal)
│   │   ├── services/api.js          # Axios backend client
│   │   ├── App.jsx                  # Main dashboard layout
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── README.md
```

---

## 4. Installation & Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Docker (optional for containerized deployment)

### Backend Setup (Local Development)

```bash
cd news-collection-engine/backend

# Create virtual environment
python -m venv .venv
# Activate on Windows:
.venv\Scripts\activate
# Activate on macOS/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run FastAPI server
uvicorn app.main:app --reload --port 8000
```
Backend will start at `http://127.0.0.1:8000` (API Docs at `http://127.0.0.1:8000/docs`).

### Frontend Setup (React + Vite)

```bash
cd news-collection-engine/frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
Frontend dashboard will start at `http://localhost:5173`.

---

## 5. Environment Variables Configuration

Created in `backend/.env`:

```ini
APP_NAME=Multi-Source News Collection Engine
ENVIRONMENT=development
DEBUG=true
DEMO_MODE=true

# Database (PostgreSQL primary, SQLite fallback if unconfigured or unreachable)
DATABASE_URL=sqlite:///./news_engine.db

# Redis Cache (Redis primary, In-memory dictionary fallback if unconfigured)
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=300

# Permitted News API Keys (Optional)
NEWSAPI_KEY=your_newsapi_key_here
GNEWS_API_KEY=your_gnews_key_here
NEWSDATA_API_KEY=your_newsdata_key_here

MAX_RETRY_ATTEMPTS=3
RETRY_BACKOFF_FACTOR=2.0
```

---

## 6. PostgreSQL & Redis Setup & Fallbacks

- **PostgreSQL**: Set `DATABASE_URL=postgresql://user:password@localhost:5432/news_db`. If PostgreSQL is offline, the engine automatically falls back to an embedded SQLite database (`sqlite:///./news_engine.db`).
- **Redis**: Set `REDIS_URL=redis://localhost:6379/0`. If Redis is unavailable, the engine seamlessly uses an in-memory dictionary cache with TTL expiration.

---

## 7. Demo Mode (Zero Credentials Required)

Set `DEMO_MODE=true` in `.env`.
In Demo Mode:
- The engine operates without requiring external API keys.
- Uses deterministic mock article data centered around **"Tata Motors EV"**.
- Simulates multi-source collection, duplicate detection, cache hits/misses, and cost tracking.
- Clearly displays **"Demo Mode Active"** in the frontend dashboard.

---

## 8. Docker Usage

Run the complete stack (PostgreSQL, Redis, FastAPI Backend, React Frontend) with one command:

```bash
cd news-collection-engine
docker compose up --build
```
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

---

## 9. REST API Endpoints & Example Curl Requests

### 1. Collect News Pipeline
`POST /api/collect-news`

```bash
curl -X POST "http://127.0.0.1:8000/api/collect-news" \
     -H "Content-Type: application/json" \
     -d '{
           "entity": "Tata Motors",
           "keywords": ["EV", "electric vehicle"],
           "location": "India",
           "category": "Automotive",
           "time_window_minutes": 60
         }'
```

### 2. Get Articles
`GET /api/articles?limit=20`

### 3. Get Registered Sources & Status
`GET /api/sources/status`

### 4. Get Engine Usage Analytics
`GET /api/usage`

### 5. Get Routing Decision Explanation
`GET /api/routing/last-decision`

### 6. Get Health Status
`GET /api/health`

---

## 10. Adding a New Source

To register a new RSS or API source dynamically **without modifying core collection engine code**:

```bash
curl -X POST "http://127.0.0.1:8000/api/sources" \
     -H "Content-Type: application/json" \
     -d '{
           "name": "Reuters Business RSS",
           "source_type": "RSS",
           "connection_method": "rss",
           "rss_url": "https://www.reutersagency.com/feed/",
           "priority": 9,
           "request_limit": 1000,
           "estimated_cost_per_request": 0.0,
           "enabled": true
         }'
```
The Source Router will automatically detect and evaluate the new source in subsequent collection runs.

---

## 11. Core Engine Mechanics

- **Recency Filtering**: Filters articles by `published_at` timestamp. Retains unknown timestamps with explicit flag `publication_time_unavailable: true`.
- **Deduplication**: Multi-stage detection (Canonical URL -> Content MD5 Hash -> Normalized Title -> Title Similarity >= 0.85). Retains primary article and records duplicate mappings in `duplicate_relationships` table.
- **Rate Limit Controller**: Tracks requests made within window, enforces quotas, sets status `RATE_LIMITED`, and executes retry logic with exponential backoff (`tenacity`).
- **Cost Tracking**: Calculates actual cost metrics (`sum(request_count * cost_per_request)`) labeled as "Estimated cost based on configured pricing".
- **Legal Access Principles**: Strictly respects API keys, quotas, rate limits, and robots.txt. No anti-bot bypass, paywall circumvention, or fake user agent rotation is performed.

---

## 12. Running Automated Tests

```bash
cd news-collection-engine/backend
pytest -v
```
All unit and integration tests (RSS, connectors, router, recency, deduplication, cache, rate limits, pipeline integration) will execute.
