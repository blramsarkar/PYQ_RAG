import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import json
import os

CHROMA_PATH = "./data/chroma_db"
COLLECTION_NAME = "pyq_questions"

_model = None
_client = None
_collection = None


def get_embedder():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_questions(parsed_data: dict, source_filename: str):
    """Embed and store questions into ChromaDB."""
    collection = get_collection()
    embedder = get_embedder()

    subject = parsed_data.get("subject", "Unknown")
    exam_type = parsed_data.get("exam_type", "Unknown")
    year = parsed_data.get("year", "Unknown")
    questions = parsed_data.get("questions", [])

    ids, embeddings, documents, metadatas = [], [], [], []

    for i, q in enumerate(questions):
        text = q.get("question_text", "").strip()
        if not text:
            continue

        uid = f"{source_filename}_{i}"
        embedding = embedder.encode(text).tolist()

        ids.append(uid)
        embeddings.append(embedding)
        documents.append(text)
        metadatas.append({
            "subject": subject,
            "exam_type": exam_type,
            "year": year,
            "topic": q.get("topic", "General"),
            "difficulty": q.get("difficulty", "Medium"),
            "marks": str(q.get("marks", "")),
            "question_number": q.get("question_number", str(i + 1)),
            "source": source_filename,
        })

    if ids:
        collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    return len(ids)


def query_questions(
    query: str,
    subject_filter: str = None,
    exam_type_filter: str = None,
    topic_filter: str = None,
    difficulty_filter: str = None,
    n_results: int = 15,
) -> List[Dict]:
    """Semantic search with optional metadata filters."""
    collection = get_collection()
    embedder = get_embedder()

    where = {}
    conditions = []
    if subject_filter and subject_filter != "All":
        conditions.append({"subject": {"$eq": subject_filter}})
    if exam_type_filter and exam_type_filter != "All":
        conditions.append({"exam_type": {"$eq": exam_type_filter}})
    if topic_filter and topic_filter != "All":
        conditions.append({"topic": {"$eq": topic_filter}})
    if difficulty_filter and difficulty_filter != "All":
        conditions.append({"difficulty": {"$eq": difficulty_filter}})

    if len(conditions) == 1:
        where = conditions[0]
    elif len(conditions) > 1:
        where = {"$and": conditions}

    query_embedding = embedder.encode(query).tolist()

    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": min(n_results, max(collection.count(), 1)),
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({"question": doc, "meta": meta, "score": round(1 - dist, 3)})
    return output


def get_all_metadata() -> List[Dict]:
    """Fetch all stored metadata for analytics."""
    collection = get_collection()
    total = collection.count()
    if total == 0:
        return []
    results = collection.get(include=["metadatas", "documents"])
    out = []
    for doc, meta in zip(results["documents"], results["metadatas"]):
        out.append({"question": doc, "meta": meta})
    return out


def get_distinct_values(field: str) -> List[str]:
    """Get unique values for a metadata field."""
    all_data = get_all_metadata()
    values = sorted(set(d["meta"].get(field, "") for d in all_data if d["meta"].get(field)))
    return values


def get_total_count() -> int:
    return get_collection().count()



def reset_collection():
    """Delete all documents from the collection."""
    global _client, _collection
    _collection = None  # invalidate cache
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    _collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )