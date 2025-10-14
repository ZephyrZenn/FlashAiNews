# FlashNews

FlashNews is a daily intelligence assistant that turns noisy RSS subscriptions into curated, AI-written briefings. Organize your sources into topical groups, let the built-in crawler gather fresh articles, and rely on modern LLMs to produce concise summaries you can skim in minutes.

PS: It's another round of information moisture. Be careful about what you see.

## Features

- **LLM-quality briefs without prompt fatigue** – Craft a single prompt once, and FlashNews uses it to generate daily group-level summaries and per-article highlights.
- **Topic-driven organization** – Split large OPML collections into thematic groups so the briefing you read reflects the way you think about news.
- **Smart clustering** – Sentence Transformers + HDBSCAN automatically cluster similar stories, helping the model elevate trends rather than repeat duplicates.

## Prerequisites

- Docker 24+ and Docker Compose v2
- OpenAI-compatible or Google Gemini API key (place in `backend/config.toml`). You can also configure it in frontend.
- Optional: Google API key if you swap models

## Quick Start (Docker Compose)

```bash
# 1. Clone the repo
 git clone https://github.com/your-org/FlashNews.git
 cd FlashNews

# 2. Create environment variables (optional – defaults provided)
 cat <<'ENV' > .env
 POSTGRES_USER=flashnews
 POSTGRES_PASSWORD=flashnews
 POSTGRES_DB=flashnews
 POSTGRES_HOST=xxx
 ENV

# 3. Provide LLM configuration
 cat <<'TOML' > backend/config.toml
 prompt = "Summarize the following news items, highlight big themes, and list actionable insights."
 brief_time = "14:20"

 [model]
 model = "gpt-4.1-mini"
 provider = "openai"
 api_key = "sk-..."
 base_url = "https://api.openai.com/v1"
 TOML

# 4. Launch everything
 cd infra/docker
 docker compose up --build -d
```

Compose provisions three services:

- `backend` – FastAPI app on port `8000`
- `frontend` – Nginx-served SPA on port `80`
- `db` – Postgres 16 with schema seeded from `backend/sql/schema.sql`

Access the app at `http://localhost`. All `/api` calls proxy to the backend container. Logs are available via `docker compose logs -f <service>`.

To target a backend running elsewhere, set `BACKEND_URL` in your `.env` before `docker compose up`. The value populates the frontend container's `BACKEND_URL` and is injected into nginx at runtime (defaults to `http://backend:8000`).

## Manual Development

### Backend

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run-backend.py
```

Run tests or scripts with the virtualenv active. The server reloads thanks to `uvicorn` when `ENV=dev`.

### Frontend

```bash
cd apps/frontend
npm install
npm run dev
```

Vite serves the SPA at `http://localhost:5173` and proxies `/api` to `http://localhost:8000` when `.env` contains `VITE_API_BASE_URL=http://localhost:8000/api`.

## Contributing

Issues and PRs welcome! Please run linting (`npm run lint` for frontend, formatters for backend) and provide test coverage for pipeline or service changes.

## License

[MIT License](LICENSE)
