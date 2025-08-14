"""
===============================================================================
MÓDULO: rag.py (Retrieval-Augmented Generation) (5)
===============================================================================
Definición:
-----------
Implementa el patrón RAG, que combina búsqueda de información relevante 
(retrieval) con generación de texto (generation) usando un LLM.

Conceptos Clave:
----------------
- Chunking: Dividir un texto largo en fragmentos (chunks) para indexarlos.
- Overlap: Superposición entre chunks para mantener el contexto.
- Metadata: Información adicional (paciente, fecha, tipo) que permite 
  filtrados más precisos en las búsquedas.

Rol en el Sistema:
------------------
- Indexar transcripciones en el vector store, creando chunks con metadata.
- Recuperar fragmentos relevantes para responder preguntas.
===============================================================================
"""
import uuid
from datetime import datetime
from app.storage import upsert_documents, query_similar
from app.logging_utils import span, logger

def chunk_text(text: str, max_chars: int = 900, overlap: int = 120):
    """
    Divide texto en fragmentos de hasta max_chars con solape 'overlap'.
    Garantiza avance y evita bucles infinitos.
    """
    text = " ".join(text.split())  # normaliza espacios
    if not text:
        return []

    chunks = []
    start = 0

    # aseguramos que el overlap no sea >= max_chars
    overlap = min(overlap, max_chars - 1)

    while start < len(text):
        end = min(len(text), start + max_chars)
        chunks.append(text[start:end])

        # nuevo start avanzando al menos 1 char
        new_start = end - overlap
        if new_start <= start:
            new_start = start + 1
        start = new_start

    return chunks

def index_transcript(transcript: str, patient_name: str | None = None, date_str: str | None = None, source_id: str | None = None):
    date_str = date_str or datetime.utcnow().strftime("%Y-%m-%d")
    source_id = source_id or str(uuid.uuid4())

    with span("INDEX: CHUNKING"):
        chunks = chunk_text(transcript)
        logger.info(f"[INDEX] chunks={len(chunks)} total_chars={len(transcript)}")

    docs = []
    for j, ch in enumerate(chunks):
        docs.append({
            "id": f"{source_id}::chunk{j}",
            "text": ch,
            "metadata": {
                "source_id": source_id,
                "patient_name": patient_name,
                "date": date_str,
                "kind": "transcript_chunk",
                "chunk_idx": j
            }
        })

    with span("INDEX: UPSERT_DOCUMENTS"):
        upsert_documents(docs)

    return {"source_id": source_id, "chunks_indexed": len(docs)}

def retrieve_chunks(query: str, filters: dict | None, k: int = 6):
    where = None  # por defecto None
    if filters and isinstance(filters, dict):
        temp_where = {}
        for key, val in filters.items():
            # Ignorar si el valor es None, dict vacío o string vacío
            if val is None or (isinstance(val, dict) and not val) or (isinstance(val, str) and not val.strip()):
                continue

            if key == "date_range" and isinstance(val, (list, tuple)) and len(val) == 2:
                temp_where["date"] = {"$gte": val[0], "$lte": val[1]}
            else:
                temp_where[key] = val

        if temp_where:  # solo usar si hay algo válido
            where = temp_where

    res = query_similar(query, where=where, top_k=k)
    return [
        {"text": r["text"], "source_id": r["metadata"].get("source_id"), "metadata": r["metadata"]}
        for r in res
    ]