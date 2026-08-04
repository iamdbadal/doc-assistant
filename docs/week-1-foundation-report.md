# Week 1 Foundation Report

## Purpose

This document summarizes what was completed in Week 1 of the doc-assistant project so a new LLM or engineer can pick up Week 2 work without re-locating the core assumptions, structure, or code paths.

The scope was foundation work only:

- Monorepo structure
- FastAPI skeleton
- Typed configuration
- Local infrastructure
- Tooling and CI
- Basic documentation and handoff readiness

## Executive Summary

The repository now has a working Week 1 foundation. The API service is scaffolded, the repo has a clear local development path, the main tooling is wired up, and the project can be synchronized with `uv sync --all-extras --dev`.

The implementation is still intentionally shallow in a few places. Week 1 established the backbone needed for Week 2 feature work, but it does not yet include the actual ingestion pipeline, embeddings pipeline, model orchestrator logic, frontend application, or hosted service integrations beyond configuration placeholders.

## Repo Structure

The repository is organized as a lightweight monorepo with the following top-level areas:

- `services/api` - FastAPI backend service
- `services/ingestion` - placeholder service boundary for document ingestion
- `services/embeddings` - placeholder service boundary for embedding generation
- `services/model-orchestrator` - placeholder service boundary for model routing and orchestration
- `services/frontend` - placeholder service boundary for the user interface
- `infra` - infrastructure-related assets and deployment prep
- `ops` - operational or runbook-oriented material
- `docs` - project documentation, including this report

Note: the exact folder name `services/model-orchestrator` is used in the repo. The Week 1 checklist mentioned a slightly different spelling in one place, but that naming difference was ignored for the purposes of completion.

## What Was Implemented

### 1. FastAPI Skeleton

The API service lives under `services/api/app`.

#### Main application entrypoint

File: `services/api/app/main.py`

Implemented behavior:

- Creates a FastAPI app instance with the configured project name
- Exposes `GET /health`
- Returns a small JSON payload for health checks
- Adds request logging middleware
- Emits structured JSON logs through a custom logging formatter

Implementation details:

- The app imports settings from `app.settings`
- A `JSONFormatter` class converts each `LogRecord` into JSON
- The logger writes `time`, `level`, `name`, and `message`
- Middleware logs request start and completion around each HTTP request

Current health response shape:

```json
{
  "status": "ok",
  "project": "Contextual Document Assistant"
}
```

#### Typed settings

File: `services/api/app/settings.py`

The settings module now uses `pydantic_settings.BaseSettings` with typed fields for the app configuration.

Configured values include:

- Project metadata
- Environment flags
- MinIO credentials and endpoint settings
- AI provider API keys
- Pinecone configuration
- Redis URL
- Logging level
- Service endpoint placeholders for vector DB, embeddings, and LLM

Important fields currently present:

- `project_name`
- `environment`
- `debug`
- `api_version`
- `minio_endpoint`
- `minio_access_key`
- `minio_secret_key`
- `minio_secure`
- `openai_api_key`
- `huggingface_api_key`
- `anthropic_api_key`
- `pinecone_api_key`
- `pinecone_index`
- `pinecone_region`
- `redis_url`
- `log_level`
- `vector_db_url`
- `embeddings_url`
- `llm_url`

Settings are loaded from `.env` via `SettingsConfigDict` with `extra="ignore"`.

### 2. API Containerization

File: `services/api/Dockerfile`

The API Dockerfile exists and currently uses a simple Python base image.

Build flow:

- Start from `python:3.11-slim`
- Set `/app` as the working directory
- Copy `requirements.txt`
- Install dependencies with `pip`
- Copy the application code into the image
- Launch the API with `uvicorn app.main:app --host 0.0.0.0 --port 8000`

This is a minimal container suitable for early development. It is not yet multi-stage or production hardened, but it is sufficient for Week 1.

### 3. Local Infrastructure

File: `docker-compose.yml`

The local compose file provides the minimum infrastructure for early development:

- MinIO for S3-compatible object storage
- Redis for caching and queue support

MinIO details:

- Uses the `minio/minio` image
- Exposes ports `9000` and `9001`
- Uses default local dev credentials
- Starts the MinIO server with the console enabled

Redis details:

- Uses `redis:alpine`
- Exposes port `6379`

No local Milvus or Chroma service is currently included. The project instead leans toward hosted vector DB usage, which is aligned with the Week 1 guidance.

### 4. Tooling

#### Project dependency definition

File: `pyproject.toml`

The project is set up for `uv`-based dependency management.

Main runtime dependencies currently include:

- `fastapi`
- `openai`
- `pinecone`
- `pydantic-settings`
- `python-dotenv`
- `sentence-transformers`

Development dependencies currently include:

- `black`
- `isort`
- `mypy`
- `pytest`
- `ruff`

The `isort` dependency was added after an initial CI mismatch was found between the workflow and the dependency set. This is now synchronized and validated with `uv sync --all-extras --dev`.

#### Pre-commit hooks

File: `.pre-commit-config.yaml`

The pre-commit setup now includes:

- `isort`
- `black`
- `ruff`
- `mypy`
- Core repository hygiene hooks from `pre-commit-hooks`
- Secret scanning with `detect-secrets`

This gives the repo a useful local quality gate before changes are committed.

#### GitHub Actions CI

File: `.github/workflows/ci.yml`

The CI workflow runs on pushes and pull requests and performs:

- Checkout
- Python setup
- `uv` setup
- Dependency sync
- Formatting check with Black
- Import sorting check with isort
- Linting with Ruff
- Type checking with MyPy
- Unit tests with Pytest

The CI job is intentionally simple and linear. It is enough for Week 1 foundation validation.

### 5. Environment Template

File: `.env.example`

The example environment file documents the expected configuration surface for local development.

It includes placeholders for:

- Project name and environment
- MinIO connection settings
- OpenAI, Hugging Face, and Anthropic API keys
- Pinecone credentials and index settings
- Vector DB, embeddings, and LLM service URLs
- Redis URL
- Logging level

This file is useful both for local setup and for Week 2 handoff, because it shows the intended configuration contract.

### 6. README Documentation

File: `README.md`

The root README now describes:

- The monorepo service boundaries
- The API, ingestion, embeddings, orchestrator, and frontend roles
- A minimal local development flow

Current quickstart guidance in the README:

1. Copy `.env.example` to `.env`
2. Start local services with `docker-compose up -d`
3. Install API dependencies inside `services/api`
4. Run the FastAPI app with `uvicorn app.main:app --reload`

### 7. Test Coverage

File: `tests/test_health.py`

There is a basic asynchronous test for the health endpoint.

What it verifies:

- `health_check()` returns a payload with `status == "ok"`
- The payload includes a non-empty `project` field

This test is minimal but confirms the basic API contract is wired correctly.

## Validation Performed

The key validation step completed for the dependency/tooling update was:

```bash
uv sync --all-extras --dev
```

That completed successfully after `isort` was added to `pyproject.toml`.

Other repo checks confirmed the expected files exist and are populated:

- API service entrypoint
- API settings module
- Dockerfile
- Compose file
- CI workflow
- Pre-commit config
- README
- Test file

## Important Gaps Still Remaining

The following items are still not implemented as actual product features and should be treated as Week 2+ work:

- Ingestion pipeline implementation
- Embedding generation service implementation
- Model orchestrator logic and provider fallback
- Frontend application implementation
- Real vector DB integration beyond configuration placeholders
- Hosted deployment configuration
- GitHub Secrets population and external account setup
- End-to-end data ingestion and retrieval flow

The repository currently has the scaffolding and configuration needed to start those tasks, but not the full workflows themselves.

## Notable Technical Observations

- The API logging middleware is currently simple and request-scoped; it is structured enough for early debugging but not yet a fully centralized logging stack.
- The Dockerfile still uses a straightforward `pip install -r requirements.txt` flow. It works for the current setup but could later be modernized to use `uv` directly or a multi-stage build.
- The project leans toward hosted vector database usage, which matches the Week 1 intent of avoiding heavy local Milvus setup.
- The repo currently has placeholder service folders for the non-API components, which is appropriate for a foundation week.

## Week 2 Handoff Notes

If a new LLM is continuing from here, the best next-step assumptions are:

1. Preserve the current monorepo layout and keep building inside the existing service boundaries.
2. Treat `services/api` as the first real integration point for end-user behavior.
3. Add real orchestration logic next, especially provider fallback for embeddings and LLM calls.
4. Decide whether the vector DB integration will target Pinecone or another hosted service and implement that path cleanly.
5. Extend the test suite beyond the health check so Week 2 changes are regression-safe.

## Current Status Summary

Week 1 foundation is effectively complete for the repo-local coding work.

What remains outside the codebase is external setup verification:

- Hosted provider signups
- API key storage in GitHub Secrets
- Staging deployment account creation

Those cannot be proven from repository contents alone.
