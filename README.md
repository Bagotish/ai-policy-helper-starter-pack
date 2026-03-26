# AI Policy & Product Helper (RAG System)

A high-performance **Retrieval-Augmented Generation (RAG)** system built to query internal company policies and product documentation. This application uses a modern AI stack to provide accurate, grounded, and multilingual responses.

## Key Features

- **RAG Architecture**: Prevents AI hallucinations by grounding responses in verified documents.
- **Multilingual Support**: Seamlessly handles queries in both English and Bahasa Melayu.
- **Vector Search**: Powered by Qdrant for lightning-fast semantic retrieval.
- **Containerized**: Fully orchestrated using Docker for easy deployment.
- **Real-time UX**: Next.js frontend with auto-scrolling chat and citation displays.

## Tech Stack

- **Frontend**: Next.js 14 (App Router), Tailwind CSS, Lucide React.
- **Backend**: FastAPI (Python 3.10+), Uvicorn.
- **Vector DB**: Qdrant (Running in Docker).
- **LLM Orchestration**: OpenRouter (GPT-4o-mini) / Custom Stub Mode.
- **Embeddings**: Local-384 (Fast and efficient CPU-based embeddings).

## Getting Started

### 1. Prerequisites

- Docker & Docker Compose installed.
- An OpenRouter API Key (Optional, system supports `stub` mode).

### 2. Environment Setup

Create a `.env` file in the root directory:

```bash
# Backend
LLM_PROVIDER=stub
OPENROUTER_API_KEY=your_key_here
LLM_MODEL=openai/gpt-4o-mini
VECTOR_STORE=qdrant
COLLECTION_NAME=policy_helper

# Frontend
NEXT_PUBLIC_API_BASE=http://localhost:8000
```
