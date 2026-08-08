# Contextual Document Assistant

A production-grade generative-AI service demonstrating data pipelines, vector databases, model orchestration, and prompt engineering.

## Architecture Structure
This monorepo is divided into distinct service boundaries:
- **API**: FastAPI backend for querying and triggering ingestion.
- **Ingestion**: ETL pipelines for text extraction and chunking.
- **Embeddings**: Vector generation and storage jobs.
- **Model Orchestrator**: LLM routing, RAG assembly, and caching.
- **Frontend**: React application for chat and admin UI.

## Local Development
1. Copy `.env.example` to `.env` and fill in your API keys.
2. Spin up local storage and caching with `docker-compose up -d`.
3. Navigate to `services/api/` and run `uv pip install -r requirements.txt`.
4. Start the development server with `uvicorn app.main:app --reload`.
