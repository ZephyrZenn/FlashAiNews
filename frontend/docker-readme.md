# Docker Deployment Instructions

## Building the Docker Image

```bash
# Default build (will use runtime environment variables)
docker build -t news-collector-frontend .

# Build with a specific API URL
docker build --build-arg VITE_API_URL=https://your-backend-api.com -t news-collector-frontend .
```

## Running the Docker Container

```bash
# Run with default configuration (uses the URL from build time)
docker run -p 80:80 news-collector-frontend

# Run with a specific backend API URL
docker run -p 80:80 -e VITE_API_URL=https://your-backend-api.com news-collector-frontend
```

## Development vs Production

- When running `npm run dev` locally, the frontend will use `http://localhost:8000` as the API URL
- In the Docker container, it will use the value provided for `VITE_API_URL` at runtime or build time

## Examples

### Local Development

```bash
npm run dev
# Uses http://localhost:8000 as API URL
```

### Production Deployment

```bash
# Build image
docker build -t news-collector-frontend .

# Run container with production API URL
docker run -p 80:80 -e VITE_API_URL=https://api.yournewscollector.com news-collector-frontend
```
