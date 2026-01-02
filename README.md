# FlashNews

FlashNews is a daily intelligence assistant that turns noisy RSS subscriptions into curated, AI-written briefings. Organize your sources into topical groups, let the built-in crawler gather fresh articles, and rely on modern LLMs to produce concise summaries you can skim in minutes.

PS: It's another round of information moisture. Be careful about what you see.

## Features

- **AI-powered briefs** – FlashNews uses modern LLMs to generate daily group-level summaries and per-article highlights with intelligent planning and execution.
- **Topic-driven organization** – Split large OPML collections into thematic groups so the briefing you read reflects the way you think about news.
- **Smart content enhancement** – Automatically searches the web to enhance important topics when RSS feeds provide limited information.

## Prerequisites

- Docker 24+ and Docker Compose v2
- PostgreSQL database (can be provided via Docker Compose)
- OpenAI-compatible or Google Gemini API key (configure in `config.toml` or via frontend)
- Optional: Tavily API key for web search enhancement (enables SEARCH_ENHANCE strategy)

## Quick Start (Docker Compose)

```bash
# 1. Clone the repo
 git clone https://github.com/your-org/FlashNews.git
 cd FlashNews

# 2. Create environment variables
 cat <<'ENV' > .env
 POSTGRES_USER=flashnews
 POSTGRES_PASSWORD=flashnews
 POSTGRES_HOST=db
 POSTGRES_DB=flashnews
 POSTGRES_PORT=5432
 TAVILY_API_KEY=your-tavily-api-key  # Optional: enables web search enhancement
 ENV

# 3. Create LLM configuration
 cp config.toml.example config.toml
 # Edit config.toml and set your API key and model settings

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

## Configuration

### Environment Variables

The following environment variables are required for the backend:

- `POSTGRES_USER` - PostgreSQL database user
- `POSTGRES_PASSWORD` - PostgreSQL database password
- `POSTGRES_HOST` - PostgreSQL database host (e.g., `localhost` or `db` for Docker)
- `POSTGRES_DB` - PostgreSQL database name
- `POSTGRES_PORT` - PostgreSQL database port (default: `5432`)

Optional environment variables:

- `TAVILY_API_KEY` - Tavily API key for web search enhancement. When provided, enables the `SEARCH_ENHANCE` strategy in the Agent pipeline, allowing the system to search the web for additional context when RSS feeds provide limited information.

You can also override model configuration via environment variables:

- `MODEL_API_KEY` - Override API key from config file
- `MODEL_BASE_URL` - Override base URL from config file
- `MODEL_NAME` - Override model name from config file
- `MODEL_PROVIDER` - Override provider from config file
- `BRIEF_TIME` - Override brief generation time from config file

### Configuration File

Create `config.toml` in the project root (copy from `config.toml.example`):

```toml
# Daily brief generation time (24-hour format)
brief_time = "08:00"

[model]
# Model configuration
model = "gpt-4"
provider = "openai"  # Options: "openai"(support all OpenAI-compatible API), "gemini"
api_key = "your-api-key"
base_url = "https://api.openai.com/v1"  # Required for OpenAI-compatible APIs
```

The configuration file supports:
- `brief_time` - Time when daily briefs are generated (format: `HH:MM`)
- `[model]` section - LLM model configuration
  - `model` - Model name (e.g., `gpt-4`, `gpt-4o-mini`, `deepseek-chat`)
  - `provider` - Provider type: `openai` or `gemini`
  - `api_key` - API key for the model provider
  - `base_url` - Base URL for the API (required for OpenAI-compatible APIs)

You can also configure these settings via the frontend settings page.

## Manual Development

### Backend

1. Set up environment variables (create `.env` file or export them):

```bash
export POSTGRES_USER=flashnews
export POSTGRES_PASSWORD=flashnews
export POSTGRES_HOST=localhost
export POSTGRES_DB=flashnews
export POSTGRES_PORT=5432
export TAVILY_API_KEY=your-tavily-api-key  # Optional
export ENV=dev  # Enables auto-reload
```

2. Install dependencies and run:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Create config.toml from example
cp config.toml.example config.toml
# Edit config.toml with your API keys

python run-backend.py
```

The server runs on `http://localhost:8000` and reloads automatically when `ENV=dev`.

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
