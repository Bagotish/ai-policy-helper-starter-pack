import time, os, hashlib, uuid, json
from typing import List, Dict, Tuple
import numpy as np
import httpx 
from .settings import settings
from .ingest import chunk_text, doc_hash
from qdrant_client import QdrantClient, models as qm

# ---- Simple local embedder ----
class LocalEmbedder:
    def __init__(self, dim: int = 384):
        self.dim = dim

    def embed(self, text: str) -> np.ndarray:
        h = hashlib.sha1(text.encode("utf-8")).digest()
        rng_seed = int.from_bytes(h[:8], "big") % (2**32-1)
        rng = np.random.default_rng(rng_seed)
        v = rng.standard_normal(self.dim).astype("float32")
        v = v / (np.linalg.norm(v) + 1e-9)
        return v

# ---- Vector stores ----
class InMemoryStore:
    def __init__(self, dim: int = 384):
        self.dim = dim
        self.vecs: List[np.ndarray] = []
        self.meta: List[Dict] = []
        self._hashes = set()

    def upsert(self, vectors: List[np.ndarray], metadatas: List[Dict]):
        for v, m in zip(vectors, metadatas):
            h = m.get("hash")
            if h and h in self._hashes: continue
            self.vecs.append(v.astype("float32"))
            self.meta.append(m)
            if h: self._hashes.add(h)

    def search(self, query: np.ndarray, k: int = 4) -> List[Tuple[float, Dict]]:
        if not self.vecs: return []
        A = np.vstack(self.vecs)
        q = query.reshape(1, -1)
        sims = (A @ q.T).ravel() / (np.linalg.norm(A, axis=1) * (np.linalg.norm(q) + 1e-9) + 1e-9)
        idx = np.argsort(-sims)[:k]
        return [(float(sims[i]), self.meta[i]) for i in idx]

class QdrantStore:
    def __init__(self, collection: str, dim: int = 384):
        self.client = QdrantClient(url="http://qdrant:6333", timeout=10.0)
        self.collection = collection
        self.dim = dim
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            self.client.get_collection(self.collection)
        except Exception:
            self.client.recreate_collection(
                collection_name=self.collection,
                vectors_config=qm.VectorParams(size=self.dim, distance=qm.Distance.COSINE)
            )

    def upsert(self, vectors: List[np.ndarray], metadatas: List[Dict]):
        points = []
        for i, (v, m) in enumerate(zip(vectors, metadatas)):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, m.get("hash") or str(i)))
            points.append(qm.PointStruct(id=point_id, vector=v.tolist(), payload=m))
        self.client.upsert(collection_name=self.collection, points=points)

    def search(self, query: np.ndarray, k: int = 4) -> List[Tuple[float, Dict]]:
        res = self.client.search(collection_name=self.collection, query_vector=query.tolist(), limit=k)
        return [(float(r.score), dict(r.payload)) for r in res]

# ---- LLM Providers ----

#version 1
# class OpenRouterLLM:
#     def __init__(self, api_key: str, model: str):
#         # Gunakan API Key dari settings/env
#         self.api_key = api_key or "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"
#         self.model = model or "openai/gpt-4o-mini"
#         self.url = "https://openrouter.ai/api/v1/chat/completions"

#     def generate(self, query: str, contexts: List[Dict]) -> str:
#         prompt = (
#             "Anda adalah pembantu polisi syarikat profesional. Jawab soalan berdasarkan rujukan sahaja. "
#             "Gunakan Bahasa Melayu yang natural.\n\n"
#             f"Soalan: {query}\n\nRujukan:\n"
#         )
#         for c in contexts:
#             prompt += f"- {c.get('title')}: {c.get('text')[:600]}\n---\n"
#         prompt += "\nJawapan:"

#         # --- FIX HEADERS DI SINI ---
#         headers = {
#             "Authorization": f"Bearer {self.api_key.strip()}",
#             "Content-Type": "application/json",
#             "HTTP-Referer": "http://localhost:3000",
#             "X-Title": "Zulhilmi RAG App",
#             "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#         }
        
#         payload = {
#             "model": self.model,
#             "messages": [{"role": "user", "content": prompt}],
#             "temperature": 0.1
#         }

#         try:
#             # Gunakan timeout yang cukup panjang untuk model yang berat
#             with httpx.Client(timeout=45.0) as client:
#                 response = client.post(self.url, headers=headers, json=payload)
                
#                 if response.status_code == 401:
#                     return f"Maaf, ralat pengesahan (Error 401). Sila pastikan API Key OpenRouter adalah sah. Sila rujuk rujukan di bawah."
                
#                 if response.status_code != 200:
#                     return f"Maaf, AI sedang sibuk (Error {response.status_code}). Sila rujuk rujukan di bawah."
                
#                 result = response.json()
#                 return result['choices'][0]['message']['content']
#         except Exception as e:
#             return f"Error: {str(e)}. Sila lihat dokumen rujukan di bawah."

# version 2
# class OpenAILLM: # Tukar nama kalau nak, atau kekalkan pun tak apa
#     def __init__(self, api_key: str, model: str):
#         self.api_key = api_key
#         self.model = model or "gpt-4o-mini"
#         # URL ASAL OPENAI
#         # self.url = "https://api.openai.com/v1/chat/completions"
#         self.url = "https://openrouter.ai/api/v1/chat/completions"

#     def generate(self, query: str, contexts: List[Dict]) -> str:
#         # Bina prompt yang sangat tegas pasal bahasa
#         prompt = (
#             "You are a professional assistant. Answer the question STRICTLY based on the provided context.\n"
#             f"LANGUAGE RULE: You MUST respond in the SAME LANGUAGE as the user's question. "
#             "If the question is in English, answer in English. If in Malay, answer in Malay.\n\n"
#             f"User Question: {query}\n\n"
#             "Context References:\n"
#         )
#         for c in contexts:
#             prompt += f"- {c.get('title')}: {c.get('text')[:600]}\n---\n"
#         prompt += "\nFinal Answer:"
#         headers = {
#             "Authorization": f"Bearer {self.api_key.strip()}",
#             "Content-Type": "application/json"
#         }
        
#         payload = {
#             "model": self.model,
#             "messages": [{"role": "user", "content": prompt}], # Line 139 yang error tadi
#             "temperature": 0.1
#         }
#         # ... (kod httpx kau sama) ...

#         try:
#             # Gunakan timeout yang cukup panjang untuk model yang berat
#             with httpx.Client(timeout=45.0) as client:
#                 response = client.post(self.url, headers=headers, json=payload)
                
#                 if response.status_code == 401:
#                     return f"Maaf, ralat pengesahan (Error 401). Sila pastikan API Key OpenRouter adalah sah. Sila rujuk rujukan di bawah."
                
#                 if response.status_code != 200:
#                     return f"Maaf, AI sedang sibuk (Error {response.status_code}). Sila rujuk rujukan di bawah."
                
#                 result = response.json()
#                 return result['choices'][0]['message']['content']
#         except Exception as e:
#             return f"Error: {str(e)}. Sila lihat dokumen rujukan di bawah."


# version 3
# class OpenRouterLLM:
#     def __init__(self, api_key: str, model: str):
#         self.api_key = api_key
#         # Model default kalau tak set dalam .env
#         self.model = model or "openai/gpt-4o-mini"
#         # URL OPENROUTER (PENTING!)

#         self.url = "https://api.openai.com/v1/chat/completions"
#         # self.url = "https://openrouter.ai/api/v1/chat/completions"

#     def generate(self, query: str, contexts: List[Dict]) -> str:
#         # Prompt yang kita dah betulkan tadi (Multilingual)
#         prompt = (
#             "You are a professional assistant. Answer the question STRICTLY based on the provided context.\n"
#             "LANGUAGE RULE: You MUST respond in the SAME LANGUAGE as the user's question.\n\n"
#             f"User Question: {query}\n\n"
#             "Context References:\n"
#         )
#         for c in contexts:
#             prompt += f"- {c.get('title')}: {c.get('text')[:600]}\n---\n"
#         prompt += "\nFinal Answer:"

#         # HEADERS KHAS UNTUK OPENROUTER
#         headers = {
#             "Authorization": f"Bearer {self.api_key.strip()}",
#             "Content-Type": "application/json",
#             "HTTP-Referer": "http://localhost:3000", # OpenRouter perlukan ni
#             "X-Title": "Zulhilmi RAG App"
#         }
        
#         payload = {
#             "model": self.model,
#             "messages": [{"role": "user", "content": prompt}],
#             "temperature": 0.1
#         }
#         try:
#             # Gunakan timeout yang cukup panjang untuk model yang berat
#             with httpx.Client(timeout=45.0) as client:
#                 response = client.post(self.url, headers=headers, json=payload)
                
#                 if response.status_code == 401:
#                     return f"Maaf, ralat pengesahan (Error 401). Sila pastikan API Key OpenRouter adalah sah. Sila rujuk rujukan di bawah."
                
#                 if response.status_code != 200:
#                     return f"Maaf, AI sedang sibuk (Error {response.status_code}). Sila rujuk rujukan di bawah."
                
#                 result = response.json()
#                 return result['choices'][0]['message']['content']
#         except Exception as e:
#             return f"Error: {str(e)}. Sila lihat dokumen rujukan di bawah."



# class StubLLM:
#     def generate(self, query: str, contexts: List[Dict]) -> str:
#         return "Answer (stub): Sistem carian dokumen berfungsi. Sila aktifkan API untuk jawapan penuh."


class OpenRouterLLM:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model or "openai/gpt-4o-mini"

        # openrouter
        # self.url = "https://openrouter.ai/api/v1/chat/completions"

        # openai
        self.url = "https://api.openai.com/v1/chat/completions"

    def generate(self, query: str, contexts: List[Dict]) -> str:
        prompt = (
            "You are a professional assistant. Answer the question STRICTLY based on the provided context.\n"
            "LANGUAGE RULE: You MUST respond in the SAME LANGUAGE as the user's question.\n\n"
            f"User Question: {query}\n\n"
            "Context References:\n"
        )
        for c in contexts:
            prompt += f"- {c.get('title')}: {c.get('text')[:600]}\n---\n"
        prompt += "\nFinal Answer:"

        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "RAG App"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5
        }
        try:
            with httpx.Client(timeout=45.0) as client:
                response = client.post(self.url, headers=headers, json=payload)
                
                if response.status_code == 401:
                    return "Sorry, authentication error (Error 401). Please ensure your API Key is valid. Refer to the documents below."
                
                if response.status_code != 200:
                    return f"Sorry, the AI is currently busy (Error {response.status_code}). Please refer to the documents below."
                
                result = response.json()
                return result['choices'][0]['message']['content']
        except Exception as e:
            return f"Error: {str(e)}. Please check the reference documents below."


class StubLLM:
    def generate(self, query: str, contexts: List[Dict]) -> str:
        lines = []
        lines = [f"Answer (stub): Based on the following sources:"]

        for c in contexts:
            file_name = c.get("title") or "Unknown_File"
            section_name = c.get("section") or "General"
            text_content = c.get("text", "").strip()
            
            # lines.append(f"{file_name} — {section_name}")
            # lines.append(f"- {section_name} {text_content}")
            lines.append(f"{text_content}")
            lines.append("")
            
        return "\n".join(lines).replace("#", "").strip()
    

# ---- RAG Orchestrator ----
class Metrics:
    def __init__(self):
        self.t_retrieval = []
        self.t_generation = []

    def add_retrieval(self, ms: float): self.t_retrieval.append(ms)
    def add_generation(self, ms: float): self.t_generation.append(ms)

    def summary(self) -> Dict:
        avg_r = sum(self.t_retrieval)/len(self.t_retrieval) if self.t_retrieval else 0.0
        avg_g = sum(self.t_generation)/len(self.t_generation) if self.t_generation else 0.0
        return {
            "avg_retrieval_latency_ms": round(avg_r, 2),
            "avg_generation_latency_ms": round(avg_g, 2),
        }

class RAGEngine:
    def __init__(self):
        self.embedder = LocalEmbedder(dim=384)
        # Vector store selection
        if settings.vector_store == "qdrant":
            try:
                self.store = QdrantStore(collection=settings.collection_name, dim=384)
            except Exception:
                self.store = InMemoryStore(dim=384)
        else:
            self.store = InMemoryStore(dim=384)

        # LLM selection
        if settings.llm_provider == "openrouter" and settings.openrouter_api_key:
            try:
                self.llm = OpenRouterLLM(
                    api_key=settings.openrouter_api_key,
                    model=settings.llm_model,
                )
                self.llm_name = f"openrouter:{settings.llm_model}"
            except Exception:
                self.llm = StubLLM()
                self.llm_name = "stub"
        else:
            self.llm = StubLLM()
            self.llm_name = "stub"

        self.metrics = Metrics()
        self._doc_titles = set()
        self._chunk_count = 0

    def ingest_chunks(self, chunks: List[Dict]) -> Tuple[int, int]:
        vectors = []
        metas = []
        doc_titles_before = set(self._doc_titles)

        for ch in chunks:
            text = ch["text"]
            h = doc_hash(text)
            meta = {
                "id": h,
                "hash": h,
                "title": ch["title"],
                "section": ch.get("section"),
                "text": text,
            }
            v = self.embedder.embed(text)
            vectors.append(v)
            metas.append(meta)
            self._doc_titles.add(ch["title"])
            self._chunk_count += 1

        self.store.upsert(vectors, metas)
        return (len(self._doc_titles) - len(doc_titles_before), len(metas))

    def retrieve(self, query: str, k: int = 4) -> List[Dict]:
        t0 = time.time()
        qv = self.embedder.embed(query)
        results = self.store.search(qv, k=k)
        self.metrics.add_retrieval((time.time()-t0)*1000.0)
        return [meta for score, meta in results]

    # def generate(self, query: str, contexts: List[Dict]) -> str:
    #     t0 = time.time()
    #     answer = self.llm.generate(query, contexts)
    #     self.metrics.add_generation((time.time()-t0)*1000.0)
    #     return answer

    def generate(self, query: str, contexts: List[Dict]) -> str:
        t0 = time.time()
        if not contexts:
            return "I could not find any relevant information in the company documents."
        answer = self.llm.generate(query, contexts)
        self.metrics.add_generation((time.time()-t0)*1000.0)
        return answer

    def stats(self) -> Dict:
        m = self.metrics.summary()
        return {
            "total_docs": len(self._doc_titles),
            "total_chunks": self._chunk_count,
            "embedding_model": settings.embedding_model,
            "llm_model": self.llm_name,
            **m
        }

# ---- Helpers ----
def build_chunks_from_docs(docs: List[Dict], chunk_size: int, overlap: int) -> List[Dict]:
    out = []
    for d in docs:
        for ch in chunk_text(d["text"], chunk_size, overlap):
            out.append({"title": d["title"], "section": d["section"], "text": ch})
    return out
