# FlashNews

We are now in the era of information explosion. It becomes impossible to know what happened in the world comprehensively as there are too many things happened and being spread at one moment.

FlashNews is a modern news aggregation and summarization platform that helps you stay informed by providing concise daily summaries of news grouped by topics of your interest.

You can categorize topics that interest you into groups. LLM will conclude daily news based on your groups. You can get all you need to know in just one page.

PS: It's another round of information moisture. Be careful about what you see.

## Features

- **News Aggregation**: Automatically collects news from various RSS feeds
- **Smart Grouping**: Organize news sources into custom groups (e.g., Tech, Finance, Sports)
- **Daily Summaries**: Generates concise summaries of news articles for each group

![Showcase](https://raw.githubusercontent.com/FaustsRep/picbed/main/notes/CleanShot%202025-05-17%20at%2012.03.32%402x.png)

## TODO

- [ ] Customized LLM Configuration. Support cutomized prompt.
- [ ] Support more models. Can switch models easily.
- [ ] Trigger generating manually
- [ ] Cutomized time to generate the report

## Prerequisites

- Docker and Docker Compose
- Google API Key / Deepseek API Key for news summarization (Support more models in the future)

## Config

Create a `.env` file in the root directory with the following variables:

```env
# Database
POSTGRES_USER=your_pg_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=ainews
POSTGRES_HOST=xxx

```

Create a `config.toml` file under `backend` directory. The provider only supports `openai`, `gemini`, `deepseek` now.

You only need to provide one model configuration here. The app would choose the model with same name as `global.default_model`. Eg. In `models.deepseek-r1`, `deepseek-r1` is the model name.

```toml
[global]
default_model = "deepseek-r1"
prompt = ""

[models.deepseek-r1]
model = "deepseek-reasoner"
api_key = "your_api_key"
base_url = "https://api.deepseek.com"
provider = "deepseek"

```

## Deployment

1. Clone the repository:

2. Create and configure the `.env` file as shown above.

3. Create a PostgresSQL and execute sql script `backend/sql/schema.sql`

4. Create `config.toml` like `config.toml.example` and configure it.

5. Build and start the containers:

```bash
docker-compose up -d
```

## Development Setup

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)
