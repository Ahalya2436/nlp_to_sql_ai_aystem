import uuid
import requests
import os
from sqlalchemy import text

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)

from core.config import settings


# =========================
# CONFIG
# =========================
EMBEDDING_API = settings.EMBEDDING_API
COLLECTION_NAME = settings.COLLECTION_NAME

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")

client = QdrantClient(
    host=QDRANT_HOST,
    port=6333
)

def extract_keywords(question: str):

    STOPWORDS = {
        "show", "get", "find", "list", "give",
        "all", "the", "of", "data", "details",
        "which", "what", "did", "is"
    }

    words = question.lower().split()

    return [
        w for w in words
        if w not in STOPWORDS and len(w) > 2
    ]


def filter_columns_dynamic(cols, question):

    keywords = extract_keywords(question)

    matched = []

    for col in cols:
        if any(k in col.lower() for k in keywords):
            matched.append(col)

    # fallback
    if not matched:
        return cols[:5]

    return matched[:8]
# =========================
# LOCAL CACHE
# =========================
TABLE_CACHE = {}
RELATIONSHIP_CACHE = {}


# =========================
# CREATE COLLECTION (SAFE)
# =========================
def create_collection():
    try:
        collections = client.get_collections().collections
        names = [c.name for c in collections]

        if COLLECTION_NAME not in names:
            print("Creating Qdrant collection...")

            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=768,  #  must match embedding model
                    distance=Distance.COSINE
                )
            )

        else:
            print("Collection already exists")

    except Exception as e:
        print("Collection error:", e)


# =========================
# EMBEDDING API
# =========================
def get_embedding(text_value: str):
    try:
        response = requests.post(
            EMBEDDING_API,
            json={"text": text_value},
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

        return data.get("embedding", [])

    except Exception as e:
        print("Embedding error:", e)
        return []


# =========================
# FETCH SCHEMA
# =========================
# =========================
# FETCH SCHEMA (UPDATED 🔥)
# =========================
def get_schema_chunks(db, database_name: str, question: str):
    try:
        query = text("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = :db
            ORDER BY table_name
        """)

        rows = db.execute(query, {"db": database_name}).fetchall()

    except Exception as e:
        print("Schema fetch error:", e)
        return []

    tables = {}

    for table, column in rows:
        tables.setdefault(table, []).append(column)

    docs = []

    for table, cols in tables.items():

        # 🔥 DYNAMIC COLUMN FILTER
        filtered_cols = filter_columns_dynamic(cols, question)

        schema_doc = f"""
Table: {table}
Description: Stores information about {table}
Relevant Columns: {", ".join(filtered_cols)}
"""

        docs.append(schema_doc.strip())

    return docs


# CHECK EMBEDDINGS EXIST
def schema_embeddings_exist(database_name):
    try:
        results = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="database",
                        match=MatchValue(value=database_name)
                    )
                ]
            ),
            limit=1
        )

        return len(results[0]) > 0

    except Exception as e:
        print("Qdrant check error:", e)
        return False


# STORE EMBEDDINGS (FIXED)
def store_schema_embeddings(db, database_name: str):

    #  ALWAYS ensure collection exists
    create_collection()

    if schema_embeddings_exist(database_name):
        print("Embeddings already exist for:", database_name)
        return

    documents = get_schema_chunks(db, database_name,question="")

    if not documents:
        print("No schema found")
        return

    points = []

    for doc in documents:

        embedding = get_embedding(doc)

        if not embedding:
            continue

        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "text": doc,
                    "database": database_name
                }
            )
        )

    if points:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )

        print(f"{database_name} schema embedded successfully")


# =========================
# KEYWORD SEARCH
# =========================
def keyword_schema_search(db, database_name, question):
    try:
        if database_name in TABLE_CACHE:
            tables = TABLE_CACHE[database_name]
        else:
            query = text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = :db
            """)

            rows = db.execute(query, {"db": database_name}).fetchall()
            tables = [r[0] for r in rows]

            TABLE_CACHE[database_name] = tables

        matched = []
        question = question.lower()

        for table in tables:
            if table.lower() in question:
                matched.append(table)

        return matched

    except Exception as e:
        print("Keyword search error:", e)
        return []


# =========================
# RELATIONSHIP EXPANSION
# =========================
def expand_with_relationships(db, database_name, schema_chunks):
    try:
        if database_name in RELATIONSHIP_CACHE:
            rows = RELATIONSHIP_CACHE[database_name]
        else:
            fk_query = text("""
                SELECT table_name, referenced_table_name
                FROM information_schema.key_column_usage
                WHERE table_schema = :db
                AND referenced_table_name IS NOT NULL
            """)

            rows = db.execute(fk_query, {"db": database_name}).fetchall()
            RELATIONSHIP_CACHE[database_name] = rows

        related = set()
        chunk_text = " ".join(schema_chunks)

        for table, ref_table in rows:
            if table in chunk_text or ref_table in chunk_text:
                related.add(table)
                related.add(ref_table)

        return related

    except Exception as e:
        print("Relationship expansion error:", e)
        return set()


# =========================
# RAG SEARCH
# =========================
def search_schema(question: str, database_name: str, db=None, top_k: int = 2):

    # Get embedding
    query_embedding = get_embedding(question)
    if not query_embedding:
        return ""

    # Vector search (ONLY for table names, not full schema)
    vector_tables = set()

    try:
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            limit=top_k,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="database",
                        match=MatchValue(value=database_name)
                    )
                ]
            )
        )

        if results and results.points:
            for point in results.points:
                text = point.payload.get("text", "")

                # Extract table name safely
                if "Table:" in text:
                    table_name = text.split("Table:")[1].split("\n")[0].strip()
                    vector_tables.add(table_name)

    except Exception as e:
        print("Vector search error:", e)

    # Keyword search (adds more tables)
    keyword_tables = set()
    if db:
        keyword_tables = set(
            keyword_schema_search(db, database_name, question)
        )

    # Merge table candidates
    selected_tables = vector_tables.union(keyword_tables)

    # fallback if nothing found
    if not selected_tables and db:
        dynamic_chunks = get_schema_chunks(db, database_name, question)
        return "\n\n".join(dynamic_chunks[:3])

    # Get CLEAN filtered schema ONLY for selected tables
    final_docs = []

    if db:
        dynamic_chunks = get_schema_chunks(db, database_name, question)

        for chunk in dynamic_chunks:
            if "Table:" in chunk:
                table_name = chunk.split("Table:")[1].split("\n")[0].strip()

                if table_name in selected_tables:
                    final_docs.append(chunk)

    # Relationship expansion (ONLY add table names, not schema)
    if db and final_docs:
        related_tables = expand_with_relationships(
            db,
            database_name,
            final_docs
        )

        for table in related_tables:
            if table not in selected_tables:
                final_docs.append(f"Related Table: {table}")

    # Remove duplicates + limit size
    seen = set()
    clean_docs = []

    for doc in final_docs:
        if doc not in seen:
            clean_docs.append(doc)
            seen.add(doc)

    return "\n\n".join(clean_docs[:5])
    
       