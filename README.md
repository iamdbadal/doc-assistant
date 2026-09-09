# Contextual Document Assistant  
A production‑grade Retrieval‑Augmented Generation (RAG) platform for secure, explainable document intelligence.

---

## 🚀 Overview

The **Contextual Document Assistant** is an end‑to‑end generative‑AI system that ingests enterprise documents, builds a retrieval layer, and serves a secure, multi‑tenant RAG assistant through a FastAPI backend and a Flutter-based cross‑platform application.

This project demonstrates real-world engineering across:

- Machine learning pipelines  
- Backend architecture  
- Vector search  
- Model orchestration  
- Flutter frontend development  
- MLOps + observability  
- CI/CD + infrastructure automation  
- Security + multi-tenancy  

---

## 🧩 Key Features

### 📄 Document Ingestion
- PDF upload from Flutter  
- OCR for scanned documents  
- Text extraction, cleaning, normalization  
- Language detection  
- Chunking into RAG‑optimized segments  
- Metadata tracking (tenant, doc type, timestamps)

### 🔍 Embeddings & Vector Store
- Batch + incremental embedding pipeline  
- Hosted or local embedding models  
- Vector DB integration (Pinecone)  
- Metadata-aware filtering

### 🧠 Retrieval & Reranking
- k‑NN semantic search  
- Optional cross‑encoder reranker  
- High‑precision retrieval for downstream LLMs

### 🤖 Generative AI Layer
- Retrieval‑Augmented Generation (RAG)  
- Provider‑agnostic LLM orchestration (OpenAI, Hugging Face, Cohere, Replicate)  
- Fallback routing + cost-aware model selection  
- Source citations + confidence scoring

### ⚙️ Backend (FastAPI)
- Async endpoints  
- Typed Pydantic models  
- JWT authentication  
- Multi-tenant isolation  
- Usage metering & rate limiting  
- Structured logging + error handling

### 📱 Frontend (Flutter)
- Cross-platform (Android, iOS, Web, Desktop)  
- Chat UI with streaming responses  
- Document upload via presigned URLs  
- Tenant-aware session management  
- Admin dashboard (usage, logs, ingestion status)

### 🛠️ MLOps & Infra
- CI/CD (GitHub Actions)  
- Kubernetes deployment manifests  
- Terraform IaC  
- Monitoring (Prometheus + Grafana)  
- OpenTelemetry tracing  
- Model registry + data versioning

---

## 🏗️ Architecture

doc-assistant/
│
├── services/
│   ├── api/                # FastAPI backend
│   ├── ingestion/          # PDF/OCR/chunking pipelines
│   ├── embeddings/         # Embedding jobs + clients
│   ├── model-orchestrator/ # LLM routing + RAG
│   └── frontend/           # Flutter app
│
├── infra/                  # Terraform, Kubernetes, Helm
├── ops/                    # Monitoring, dashboards, runbooks
├── tests/                  # Unit + integration tests
├── docs/                   # Architecture diagrams, design docs
└── README.md


---

## ⚙️ Tech Stack

### Backend
- FastAPI  
- Python 3.10+  
- Pydantic  
- Async I/O (httpx, asyncio)

### ML & RAG
- Hugging Face / Cohere / OpenAI embeddings  
- Pinecone / Weaviate / Milvus vector DB  
- Hosted LLMs (OpenAI, HF, Cohere, Replicate)

### Frontend (Flutter)
- Flutter 3.x  
- Dart  
- Riverpod / Bloc  
- Dio / http for API calls  
- SSE/WebSockets for streaming  
- Cross-platform deployment

### Infra & Ops
- Docker  
- Kubernetes (AKS/EKS/GKE)  
- Terraform  
- GitHub Actions  
- Prometheus + Grafana  
- OpenTelemetry  
- MinIO or S3 storage

---

## 🔐 Security & Multi‑Tenancy

- JWT authentication  
- Tenant isolation at:
  - Storage layer (bucket prefixes)
  - Vector DB namespaces
  - Database rows  
- Rate limiting  
- Audit logs for queries + model outputs  
- Encryption in transit & at rest  

---

## 🧠 RAG Pipeline

1. User query → embed  
2. Vector DB search → top‑k chunks  
3. Optional reranking  
4. Prompt assembly (context + instructions)  
5. LLM generation  
6. Post‑processing (citations, confidence)  
7. Streaming response to Flutter app  

---

## 📡 API Endpoints

### Core
- `POST /v1/upload` — upload document  
- `POST /v1/ingest` — trigger ingestion  
- `POST /v1/query` — RAG query  
- `GET /v1/docs/{doc_id}` — metadata + status  

### Auth
- `POST /auth/signup`  
- `POST /auth/login`  
- `POST /auth/refresh`

### Admin
- `GET /v1/metrics` — usage, cost, latency  
- `GET /v1/tenants` — tenant management  

---

## 📱 Flutter Frontend

### Features
- Cross-platform chat interface  
- Real-time streaming responses  
- Document upload via presigned URLs  
- Tenant-aware session handling  
- Admin dashboard for:
  - Usage metrics  
  - Ingestion status  
  - Logs  

### Architecture
- Clean Architecture  
- Riverpod/Bloc for state management  
- Repository pattern for API calls  
- Error handling + retry logic  
- Secure storage for JWT tokens  

---

## 🧪 Testing

- Unit tests (pytest + Flutter test)  
- Integration tests with ephemeral containers  
- RAG quality tests (recall/precision thresholds)  
- Mocked LLM + embedding providers for CI stability  

---

## 📈 Observability

### Metrics
- Request latency  
- Embedding latency  
- Vector search latency  
- Token usage  
- Error rates  

### Tracing
- Ingestion → embeddings → retrieval → LLM  
- Correlation IDs across services  

### Dashboards
- Grafana panels for:
  - Latency  
  - Throughput  
  - Cost  
  - Model performance  

---

## 🚀 Deployment

### Staging
- Fly.io / Render free tier  
- GitHub Actions deploy pipeline  
- Flutter web hosted on Vercel or Firebase Hosting  

### Production
- Kubernetes cluster  
- Autoscaling (HPA)  
- Secrets via Vault or cloud secret manager  
- Model registry + versioning  

---

## 🗺️ Roadmap

### Completed
- Full ingestion pipeline  
- Embeddings + vector DB integration  
- RAG pipeline  
- Multi‑tenant backend  
- Flutter frontend  
- CI/CD  
- Monitoring + tracing  
- Staging deployment  

### Future Enhancements
- Self‑hosted LLMs (Llama, Mistral)  
- Advanced hallucination detection  
- Fine‑tuned rerankers  
- Document summarization + Q&A indexing  
- RBAC (role-based access control)  

---

## 🎥 Demo Flow

1. Upload a PDF from Flutter  
2. Backend stores file → ingestion pipeline runs  
3. Embeddings generated → stored in vector DB (Pinecone)  
4. User queries assistant  
5. RAG retrieves relevant chunks  
6. LLM generates answer with citations  
7. Flutter streams response in real time  

---

## 📝 License

MIT or Apache‑2.0

---

