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
- Metadata: Información adicional (paciente, fecha, tipo, age) que permite 
  filtrados más precisos en las búsquedas.

Rol en el Sistema:
------------------
- Indexar transcripciones en el vector store, creando chunks con metadata.
- Recuperar fragmentos relevantes para responder preguntas.
===============================================================================
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.storage import upsert_documents, query_similar
from app.logging_utils import span, logger


def chunk_text(text: str, max_chars: int = 900, overlap: int = 120) -> List[str]:
    """
    Divide texto en fragmentos de hasta max_chars con solape 'overlap'.
    Garantiza avance y evita bucles infinitos.
    """
    text = " ".join(text.split())  # normaliza espacios
    if not text:
        return []

    chunks: List[str] = []
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


def index_transcript(
    transcript: str,
    patient_name: Optional[str] = None,
    date_str: Optional[str] = None,
    age: Optional[int] = None,
    source_id: Optional[str] = None,
):
    date_str = date_str or datetime.utcnow().strftime("%Y-%m-%d")
    source_id = source_id or str(uuid.uuid4())

    with span("INDEX: CHUNKING"):
        chunks = chunk_text(transcript)
        logger.info(f"[INDEX] chunks={len(chunks)} total_chars={len(transcript)}")

    docs: List[Dict[str, Any]] = []
    for j, ch in enumerate(chunks):
        docs.append({
            "id": f"{source_id}::chunk{j}",
            "text": ch,
            "metadata": {
                "source_id": source_id,
                "patient_name": patient_name,
                "date": date_str,
                "age": age,
                "kind": "transcript_chunk",
                "chunk_idx": j
            }
        })

    with span("INDEX: UPSERT_DOCUMENTS"):
        upsert_documents(docs)

    return {"source_id": source_id, "chunks_indexed": len(docs)}


# ---------------------- Filtros robustos para retrieve ----------------------

_ALLOWED_OPS = {"$eq", "$ne", "$gt", "$gte", "$lt", "$lte", "$in", "$nin", "$contains"}

def _coerce_filter_value(val: Any):
    """
    - Si es escalar (str/int/float/bool) => {"$eq": val}
    - Si es dict con operadores permitidos => lo deja pasar
    - Cualquier otra cosa => None (se ignora)
    """
    if isinstance(val, (str, int, float, bool)):
        return {"$eq": val}
    if isinstance(val, dict) and val:
        ops = set(val.keys())
        if ops.issubset(_ALLOWED_OPS):
            return val
        return None
    return None


def retrieve_chunks(query: str, filters: Dict[str, Any] | None, k: int = 6):
    where: Optional[Dict[str, Any]] = None

    if filters and isinstance(filters, dict):
        temp_where: Dict[str, Any] = {}

        for key, val in filters.items():
            # Ignorar si el valor es None, dict vacío o string vacío
            if val is None or (isinstance(val, dict) and not val) or (isinstance(val, str) and not val.strip()):
                continue

            # Rango de fechas especial -> convierte a operadores
            if key == "date_range" and isinstance(val, (list, tuple)) and len(val) == 2:
                temp_where["date"] = {"$gte": val[0], "$lte": val[1]}
                continue

            coerced = _coerce_filter_value(val)
            if coerced is not None:
                temp_where[key] = coerced

        if temp_where:  # solo usar si hay algo válido
            where = temp_where

    res = query_similar(query, where=where, top_k=k)
    # salida simplificada para el LLM
    return [
        {"text": r["text"], "source_id": r["metadata"].get("source_id"), "metadata": r["metadata"]}
        for r in res
    ]