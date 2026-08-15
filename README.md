# weather_basic_app

Small Flask app that shows current weather for a city (OpenWeatherMap).
UI background changes with the weather; build version shown in the corner.

## Run locally

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export OPENWEATHER_API_KEY=<your_key>
python app.py            # http://localhost:8080
```

## MCP server

An MCP server exposes this app's weather data as tools for AI clients
(Claude Code, Claude Desktop). See the sub-page:
**[weather_mcp/README.md](weather_mcp/README.md)** — how it's built and how to
connect a client.

## Run with Docker

```bash
docker build -t weather --build-arg APP_VERSION=local .
docker run -p 8080:8080 -e OPENWEATHER_API_KEY=<your_key> weather
```

## Config (env vars)

| Var | Purpose | Default |
|-----|---------|---------|
| `OPENWEATHER_API_KEY` | API key (required) | — |
| `DEFAULT_CITY` | city on first load | `Lucknow` |
| `APP_VERSION` | version shown in UI | `dev` |
| `FLASK_DEBUG` | `true` to enable debug | `false` |

## CI/CD — GitHub Actions

Workflow: `.github/workflows/docker-publish.yml`. One pipeline that builds and
publishes the Docker image to Docker Hub (`manukoli1986/weather`).

**Triggers:** push to `master`, git tag `v*.*.*`, manual (`workflow_dispatch`),
and PRs (build-only, no push).

**Steps:** checkout → Buildx → login → build (with layer cache) → push → smoke
test (runs the image with the API key and hits `/`).

**Tags pushed:**

| Trigger | Tags |
|---------|------|
| push to `master` | `v1.0.<run_number>` (auto-increment), `latest`, `sha-<short>` |
| tag `v1.2.3` | `1.2.3`, `1.2`, `1`, `latest` |

The auto-increment version is also baked into the image and shown in the UI
footer, so you can see which build is running.

**Required repo secrets:** `DOCKERHUB_TOKEN`, `OPENWEATHER_API_KEY`.
