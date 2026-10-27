# AI Autonomous Testing Agent

> **An AI-powered platform that autonomously generates, executes, and analyses web application tests — powered by GPT-4o and Playwright.**

---

## ✨ Feature Highlights

| Feature | Description |
|---|---|
| 🤖 AI Test Generation | GPT-4o / Gemini generates Playwright test scripts from natural language |
| 🌐 Browser Automation | Headless Chromium execution via Playwright |
| 📸 Visual Evidence | Automatic screenshots & video recording per test run |
| 🐛 Defect Detection | AI-powered root cause analysis for failures |
| 📊 Allure Reports | Rich HTML reports with trends, steps, and attachments |
| 🔄 Real-time Updates | WebSocket-based live test progress dashboard |
| 🧠 Vector Memory | ChromaDB stores test embeddings for similarity search |
| 🔐 Auth & RBAC | JWT authentication with role-based access control |

---

## 🏗️ Architecture

```
                        ┌──────────────────────────────────┐
                        │          Nginx (Port 80)          │
                        │  Reverse Proxy + Rate Limiting    │
                        └────┬─────────────┬───────────────┘
                             │             │
              ┌──────────────▼──┐   ┌──────▼──────────────┐
              │  Next.js UI     │   │   FastAPI Backend    │
              │  (Port 3000)    │   │   (Port 8000)        │
              └─────────────────┘   └────┬────────┬────────┘
                                         │        │
                           ┌─────────────▼──┐  ┌──▼────────────┐
                           │  PostgreSQL 16  │  │   Redis 7     │
                           │  (Primary DB)   │  │  (Queue/Cache)│
                           └─────────────────┘  └───────────────┘
                                         │
                           ┌─────────────▼──┐  ┌───────────────┐
                           │   ChromaDB      │  │  Allure (5050)│
                           │ (Vector Store)  │  │  Reports UI   │
                           └─────────────────┘  └───────────────┘
```

---

## 📋 Prerequisites

- **Docker** 24+ and **Docker Compose** v2.20+
- **Git**
- *(Optional for local dev)* Python 3.11+, Node.js 18+

---

## 🚀 Quick Start (3 Steps)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/ai-testing-agent.git
cd ai-testing-agent

# 2. Configure environment variables
cp .env.example .env
# Edit .env — set OPENAI_API_KEY and POSTGRES_PASSWORD at minimum

# 3. Start all services
docker compose up -d
```

Open **http://localhost** in your browser. 🎉

| Service | URL |
|---|---|
| Dashboard | http://localhost |
| API Docs | http://localhost/api/docs |
| Allure Reports | http://localhost/allure |
| API (direct) | http://localhost:8000/docs |

---

## 🛠️ Development Setup

### Backend (FastAPI)

```bash
cd backend

# Create virtualenv
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Alembic migrations
alembic upgrade head

# Start dev server with hot-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Start dev server with hot-reload
npm run dev
```

### Install Playwright Browsers (local runs)

```bash
playwright install chromium
playwright install-deps chromium
```

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `POSTGRES_PASSWORD` | ✅ | — | PostgreSQL password |
| `OPENAI_API_KEY` | ✅* | — | OpenAI API key (* or Gemini) |
| `GEMINI_API_KEY` | ✅* | — | Gemini API key |
| `AI_PROVIDER` | ✅ | `openai` | `openai` \| `gemini` |
| `SECRET_KEY` | ✅ | — | JWT signing secret (min 32 chars) |
| `DATABASE_URL` | ✅ | see .env.example | SQLAlchemy DSN |
| `REDIS_URL` | ✅ | `redis://redis:6379` | Redis connection URL |
| `NEXT_PUBLIC_API_URL` | ✅ | `http://localhost/api` | Frontend API base URL |
| `PLAYWRIGHT_HEADLESS` | ❌ | `true` | Set `false` for local debugging |
| `LOG_LEVEL` | ❌ | `INFO` | `DEBUG\|INFO\|WARNING\|ERROR` |
| `ENVIRONMENT` | ❌ | `development` | `development\|staging\|production` |

---

## 📡 API Documentation

Interactive Swagger UI: **http://localhost/api/docs**
ReDoc: **http://localhost/api/redoc**

### Key Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/projects/` | Create a new test project |
| `POST` | `/api/v1/test-runs/` | Start a test run |
| `GET`  | `/api/v1/test-runs/{id}` | Get run status & results |
| `WS`   | `/ws/test-runs/{id}` | Real-time progress stream |
| `GET`  | `/api/v1/files/screenshots/{f}` | Download screenshot |
| `GET`  | `/api/v1/files/videos/{f}` | Download video recording |

---

## 🧰 Technology Stack

| Layer | Technology |
|---|---|
| **AI/ML** | OpenAI GPT-4o, Google Gemini, ChromaDB |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2, Alembic |
| **Browser Automation** | Playwright (Chromium) |
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS |
| **Database** | PostgreSQL 16 |
| **Cache / Queue** | Redis 7 |
| **Reports** | Allure Framework |
| **Proxy** | Nginx 1.25 |
| **Containers** | Docker, Docker Compose, Kubernetes |
| **CI/CD** | GitHub Actions |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit with conventional commits: `git commit -m 'feat: add amazing feature'`
4. Push to your fork: `git push origin feature/amazing-feature`
5. Open a Pull Request against `main`

### Code Standards

- **Python**: Black formatter, flake8, isort, mypy type hints
- **TypeScript**: ESLint + Prettier, strict mode enabled
- **Tests**: ≥70% coverage required to merge
- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/) format

---

## 📜 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ❤️ by the AI Testing Agent Team*
