"""
Semantic matcher — swap backends via MATCHER_BACKEND in .env:
  local  → all-mpnet-base-v2  (free, runs on your machine, no internet needed)
  openai → text-embedding-3-small  (OpenAI API, needs OPENAI_API_KEY)
"""
import numpy as np
from config import (
    TARGET_ROLE_DESCRIPTIONS, MATCH_THRESHOLD,
    ENTRY_LEVEL_KEYWORDS, SENIOR_KEYWORDS,
    MATCHER_BACKEND, OPENAI_API_KEY,
)

_TARGET_LABELS = [
    "AI Engineer",
    "ML Engineer",
    "Software Engineer",
    "Data Scientist",
    "Data Analyst",
    "Data Engineer",
]

# ── Local backend state ──────────────────────────────────────────────────────
_local_model = None
_local_target_embeddings = None

# ── OpenAI backend state ─────────────────────────────────────────────────────
_openai_client = None
_openai_target_embeddings = None


def _get_local():
    global _local_model, _local_target_embeddings
    if _local_model is None:
        from sentence_transformers import SentenceTransformer
        print("[matcher] Loading all-mpnet-base-v2 (first run downloads ~420MB)...")
        _local_model = SentenceTransformer("all-mpnet-base-v2")
        _local_target_embeddings = _local_model.encode(
            TARGET_ROLE_DESCRIPTIONS, normalize_embeddings=True
        )
        print("[matcher] Local model ready.")
    return _local_model, _local_target_embeddings


def _get_openai():
    global _openai_client, _openai_target_embeddings
    if _openai_client is None:
        if not OPENAI_API_KEY:
            raise ValueError("MATCHER_BACKEND=openai but OPENAI_API_KEY is not set in .env")
        from openai import OpenAI
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
        resp = _openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=TARGET_ROLE_DESCRIPTIONS,
        )
        vecs = [e.embedding for e in resp.data]
        _openai_target_embeddings = np.array(vecs, dtype="float32")
        norms = np.linalg.norm(_openai_target_embeddings, axis=1, keepdims=True)
        _openai_target_embeddings = _openai_target_embeddings / norms
        print("[matcher] OpenAI embeddings ready.")
    return _openai_client, _openai_target_embeddings


def _embed(texts: list[str]) -> np.ndarray:
    if MATCHER_BACKEND == "openai":
        client, _ = _get_openai()
        resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
        vecs = np.array([e.embedding for e in resp.data], dtype="float32")
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / norms
    else:
        model, _ = _get_local()
        return model.encode(texts, normalize_embeddings=True)


def _target_embeddings() -> np.ndarray:
    if MATCHER_BACKEND == "openai":
        _, embs = _get_openai()
    else:
        _, embs = _get_local()
    return embs


def compute_match(title: str, description: str = "") -> tuple[float, str]:
    """Returns (score 0-1, matched_role_label). Empty label means below threshold."""
    text = f"{title}. {description[:600]}" if description else title
    job_emb = _embed([text])
    target_emb = _target_embeddings()
    similarities = np.dot(job_emb, target_emb.T)[0]
    best_idx = int(np.argmax(similarities))
    best_score = float(similarities[best_idx])
    matched_role = _TARGET_LABELS[best_idx] if best_score >= MATCH_THRESHOLD else ""
    return round(best_score, 3), matched_role


def detect_seniority(title: str, description: str = "") -> str:
    text = f"{title} {description[:300]}".lower()
    if any(kw in text for kw in ["intern", "internship", "co-op", "coop"]):
        return "internship"
    if any(kw in text for kw in ["new grad", "new graduate", "new college grad", "recent grad"]):
        return "new_grad"
    if any(kw in text for kw in ["entry level", "entry-level", "early career"]):
        return "entry_level"
    if any(kw in text for kw in ["junior", "associate"]):
        return "junior"
    if any(kw in text for kw in SENIOR_KEYWORDS):
        return "senior+"
    return "unspecified"


def is_match(title: str, description: str = "") -> bool:
    score, _ = compute_match(title, description)
    return score >= MATCH_THRESHOLD
