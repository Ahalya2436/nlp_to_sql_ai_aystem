import uuid
from qdrant_client.models import VectorParams, Distance, PointStruct

from core.qdrant import get_qdrant_client
from services.schema_vector_services import get_embedding
from prompt.sql_examples import SQL_EXAMPLES

# -----------------------------
# INIT
# -----------------------------
client = get_qdrant_client()
COLLECTION = "sql_examples"

# Prevent duplicate inserts
EXAMPLE_CACHE = False


# -----------------------------
# CREATE COLLECTION
# -----------------------------
def create_collection():
    try:
        collections = client.get_collections().collections
        names = [c.name for c in collections]

        if COLLECTION not in names:
            client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(
                    size=768,
                    distance=Distance.COSINE
                )
            )
            print(f"[Qdrant] Created collection: {COLLECTION}")
        else:
            print(f"[Qdrant] Collection exists: {COLLECTION}")

    except Exception as e:
        print("Collection creation error:", e)


# -----------------------------
# STORE EXAMPLES (SAFE + CACHE)
# -----------------------------
def store_examples():
    global EXAMPLE_CACHE

    if EXAMPLE_CACHE:
        print("[Qdrant] Examples already stored")
        return

    points = []

    for ex in SQL_EXAMPLES:
        try:
            text = f"{ex['question']} {ex['sql']}"

            emb = get_embedding(text)

            if not emb:
                continue

            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),   # ✅ Correct ID format
                    vector=emb,
                    payload=ex
                )
            )

        except Exception as e:
            print("Example processing error:", e)
            continue

    try:
        if points:
            client.upsert(
                collection_name=COLLECTION,
                points=points
            )
            print("[Qdrant] SQL examples stored successfully")

        EXAMPLE_CACHE = True

    except Exception as e:
        print("Upsert error:", e)


# -----------------------------
# SEARCH EXAMPLES
# -----------------------------
def search_examples(question, top_k=3):

    emb = get_embedding(question)

    if not emb:
        return []

    try:
        results = client.query_points(
            collection_name=COLLECTION,
            query=emb,
            limit=top_k
        )

        if not results or not results.points:
            return []

        examples = []

        for p in results.points:
            examples.append({
                "question": p.payload.get("question", ""),
                "sql": p.payload.get("sql", "")
            })

        return examples

    except Exception as e:
        print("Search error:", e)
        return []