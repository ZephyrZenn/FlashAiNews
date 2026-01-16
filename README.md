# FlashNews

FlashNews is a daily intelligence assistant that turns noisy RSS subscriptions into curated, AI-written briefings. Organize your sources into topical groups, let the built-in crawler gather fresh articles, and rely on modern LLMs to produce concise summaries you can skim in minutes.

PS: It's another round of information moisture. Be careful about what you see.

## Features

- **AI-powered briefs** – FlashNews uses modern LLMs to generate daily group-level summaries and per-article highlights with intelligent planning and execution.
- **Topic-driven organization** – Split large OPML collections into thematic groups so the briefing you read reflects the way you think about news.
- **Smart content enhancement** – Automatically searches the web to enhance important topics when RSS feeds provide limited information.
- **Semantic memory search** – Vector-based semantic search enables the system to find relevant historical summaries by meaning, not just keywords. This helps avoid duplicate content and provides better context for ongoing stories.

## Prerequisites

- Docker 24+ and Docker Compose v2
- PostgreSQL database (can be provided via Docker Compose)
  - **For vector search**: PostgreSQL with pgvector extension installed (see [Vector Search Setup](#vector-search-setup))
- OpenAI-compatible or Google Gemini API key (configure in `config.toml` or via frontend)
- Optional: Tavily API key for web search enhancement (enables SEARCH_ENHANCE strategy)
- Optional: Embedding API key for semantic memory search (see [Vector Search Setup](#vector-search-setup))

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
 
 # Set API key for your chosen provider (choose one):
 OPENAI_API_KEY=sk-your-openai-api-key
 # DEEPSEEK_API_KEY=your-deepseek-api-key
 # GEMINI_API_KEY=your-gemini-api-key
 # MODEL_API_KEY=your-custom-api-key  # For "other" provider
 
 TAVILY_API_KEY=your-tavily-api-key  # Optional: enables web search enhancement
 
 # Optional: Embedding service for vector search
 EMBEDDING_API_KEY=sk-your-openai-api-key  # Required for vector search
 EMBEDDING_BASE_URL=https://api.openai.com/v1  # Optional
 EMBEDDING_MODEL=text-embedding-3-small  # Optional
 ENV

# 3. Create LLM configuration
 cp config.toml.example config.toml
 # Edit config.toml to set model name and provider

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

**Note for vector search**: If you want to use vector search, ensure your PostgreSQL image includes pgvector extension. You may need to use `pgvector/pgvector` image or modify the Docker Compose file to install the extension. After starting the services, run the migration script to enable vector search (see [Vector Search Setup](#vector-search-setup)).

## Configuration

### Environment Variables

The following environment variables are required for the backend:

- `POSTGRES_USER` - PostgreSQL database user
- `POSTGRES_PASSWORD` - PostgreSQL database password
- `POSTGRES_HOST` - PostgreSQL database host (e.g., `localhost` or `db` for Docker)
- `POSTGRES_DB` - PostgreSQL database name
- `POSTGRES_PORT` - PostgreSQL database port (default: `5432`)

**API Keys** (set based on your provider):

- `OPENAI_API_KEY` - API key for OpenAI provider
- `DEEPSEEK_API_KEY` - API key for Deepseek provider
- `GEMINI_API_KEY` - API key for Google Gemini provider
- `MODEL_API_KEY` - API key for "other" OpenAI-compatible providers

Optional environment variables:

- `TAVILY_API_KEY` - Tavily API key for web search enhancement. When provided, enables the `SEARCH_ENHANCE` strategy in the Agent pipeline, allowing the system to search the web for additional context when RSS feeds provide limited information.

**Embedding Service** (for vector search):

- `EMBEDDING_API_KEY` - API key for embedding service (required for vector search). Must be an OpenAI-compatible API key.
- `EMBEDDING_BASE_URL` - Base URL for embedding service (optional, defaults to OpenAI API URL)
- `EMBEDDING_MODEL` - Embedding model name (optional, default: `text-embedding-3-small`)
  - Supported models: `text-embedding-3-small` (1536 dim), `text-embedding-3-large` (3072 dim), `text-embedding-ada-002` (1536 dim)

You can also override model configuration via environment variables:

- `MODEL_NAME` - Override model name from config file
- `MODEL_PROVIDER` - Override provider from config file
- `MODEL_BASE_URL` - Override base URL (only used for "other" provider)

### Configuration File

Create `config.toml` in the project root (copy from `config.toml.example`):

```toml
[model]
# Model name to use
model = "gpt-4"

# Provider options: "openai", "deepseek", "gemini", "other"
provider = "openai"

# Base URL is automatically determined for built-in providers:
#   - openai: https://api.openai.com/v1
#   - deepseek: https://api.deepseek.com
#   - gemini: (uses Google SDK)
#
# Only required when provider = "other":
# base_url = "https://your-custom-api.com/v1"
```

The configuration file supports:
- `[model]` section - LLM model configuration
  - `model` - Model name (e.g., `gpt-4`, `gpt-4o-mini`, `deepseek-chat`)
  - `provider` - Provider type: `openai`, `deepseek`, `gemini`, or `other`
  - `base_url` - Custom API base URL (only required for `other` provider)

**Note**: API keys are managed via environment variables, not in the config file. This improves security by keeping secrets out of configuration files.

Schedule management (daily brief generation times) is configured via the frontend settings page and stored in the database.

You can also configure model name and provider via the frontend settings page.

## Vector Search Setup

FlashNews supports semantic search using vector embeddings, which allows the system to find relevant historical summaries by meaning rather than just keyword matching. This feature requires:

1. **PostgreSQL with pgvector extension**
   - For Docker: Use `pgvector/pgvector` image or install the extension manually
   - For managed services: Ensure pgvector is available (e.g., Supabase, Neon support it)
   - For local PostgreSQL: Install the extension:
     ```bash
     # On Ubuntu/Debian
     sudo apt-get install postgresql-16-pgvector
     
     # Or compile from source
     git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
     cd pgvector
     make
     sudo make install
     ```

2. **Run database migration**
   ```bash
   # Connect to your PostgreSQL database and run:
   psql -U flashnews -d flashnews -f infra/sql/migrations/001_add_vector_search.sql
   ```
   
   This migration:
   - Enables the `vector` extension
   - Adds `embedding` column to `summary_memories` table
   - Creates HNSW index for efficient similarity search

3. **Configure embedding service**
   ```bash
   # Set embedding API key (required)
   export EMBEDDING_API_KEY=sk-your-openai-api-key
   
   # Optional: Set custom base URL
   export EMBEDDING_BASE_URL=https://api.openai.com/v1
   
   # Optional: Set embedding model (default: text-embedding-3-small)
   export EMBEDDING_MODEL=text-embedding-3-small
   ```

4. **Backfill existing memories** (optional)
   
   If you have existing summary memories without embeddings, you can generate them:
   ```python
   from agent.tools import backfill_embeddings
   
   # Generate embeddings for all existing memories
   await backfill_embeddings(batch_size=50)
   
   # Or limit the number of records
   await backfill_embeddings(batch_size=50, max_records=100)
   ```

### How Vector Search Works

- **Automatic embedding generation**: When new summaries are saved, embeddings are automatically generated from `topic + reasoning + content summary` (content is truncated to 300 characters for efficiency)
- **Semantic search**: The `search_memory` tool uses cosine similarity to find relevant historical summaries
- **Fallback**: If embedding service is not configured, the system automatically falls back to keyword-based search (ILIKE matching)
- **Benefits**: 
  - Better understanding of semantic relationships (e.g., "AI" matches "artificial intelligence")
  - Avoids duplicate content by detecting similar summaries
  - Provides better context for ongoing stories

## Manual Development

### Backend

1. Set up environment variables (create `.env` file or export them):

```bash
export POSTGRES_USER=flashnews
export POSTGRES_PASSWORD=flashnews
export POSTGRES_HOST=localhost
export POSTGRES_DB=flashnews
export POSTGRES_PORT=5432

# Set API key for your chosen provider (choose one):
export OPENAI_API_KEY=sk-your-openai-api-key
# export DEEPSEEK_API_KEY=your-deepseek-api-key
# export GEMINI_API_KEY=your-gemini-api-key
# export MODEL_API_KEY=your-custom-api-key  # For "other" provider

export TAVILY_API_KEY=your-tavily-api-key  # Optional: enables web search enhancement

# Optional: Embedding service for vector search
export EMBEDDING_API_KEY=sk-your-openai-api-key  # Required for vector search
export EMBEDDING_BASE_URL=https://api.openai.com/v1  # Optional
export EMBEDDING_MODEL=text-embedding-3-small  # Optional, default: text-embedding-3-small

export ENV=dev  # Enables auto-reload
```

2. Install dependencies and run:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Create config.toml from example
cp config.toml.example config.toml
# Edit config.toml to set model name and provider

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
