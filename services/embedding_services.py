import requests
import hashlib
from core.config import settings

# -----------------------------
# CACHE STORAGE
# -----------------------------
EMBEDDING_CACHE = {}

EMBEDDING_API = settings.EMBEDDING_API


# -----------------------------
# GENERATE CACHE KEY
# -----------------------------
def _get_cache_key(text: str):
    return hashlib.md5(text.encode()).hexdigest()


# -----------------------------
# GET EMBEDDING (WITH CACHE)
# -----------------------------
def get_embedding(text: str):

    key = _get_cache_key(text)

    # -----------------------------
    # CACHE HIT
    # -----------------------------
    if key in EMBEDDING_CACHE:
        print("Embedding cache hit ")
        return EMBEDDING_CACHE[key]

    print("Embedding cache miss  → calling API")

    try:
        response = requests.post(
            EMBEDDING_API,
            json={"text": text},
            timeout=5
        )

        response.raise_for_status()
        embedding = response.json().get("embedding", [])

        if embedding:
            EMBEDDING_CACHE[key] = embedding  # store in cache

        return embedding

    except Exception as e:
        print("Embedding error:", e)
        return []


# -----------------------------
# BATCH EMBEDDING (VERY IMPORTANT)
# -----------------------------
def get_embeddings_batch(texts: list):

    results = []
    uncached_texts = []
    uncached_keys = []

    # -----------------------------
    # CHECK CACHE FIRST
    # -----------------------------
    for text in texts:
        key = _get_cache_key(text)

        if key in EMBEDDING_CACHE:
            results.append(EMBEDDING_CACHE[key])
        else:
            results.append(None)
            uncached_texts.append(text)
            uncached_keys.append(key)

    # -----------------------------
    # CALL API FOR UNCACHED
    # -----------------------------
    if uncached_texts:
        try:
            response = requests.post(
                EMBEDDING_API,
                json={"texts": uncached_texts},  # batch API
                timeout=10
            )

            response.raise_for_status()
            embeddings = response.json().get("embeddings", [])

            for key, emb in zip(uncached_keys, embeddings):
                EMBEDDING_CACHE[key] = emb

        except Exception as e:
            print("Batch embedding error:", e)

    # -----------------------------
    # FINAL RESULT
    # -----------------------------
    final = []
    for text in texts:
        key = _get_cache_key(text)
        final.append(EMBEDDING_CACHE.get(key, []))

    return final


# -----------------------------
# CLEAR CACHE
# -----------------------------
def clear_embedding_cache(text: str = None):

    if text:
        key = _get_cache_key(text)
        EMBEDDING_CACHE.pop(key, None)
        print(f"[CACHE CLEARED] {text[:30]}...")
    else:
        EMBEDDING_CACHE.clear()
        print("[CACHE CLEARED] All embeddings")