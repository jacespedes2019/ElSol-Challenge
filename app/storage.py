"""
===============================================================================
MÓDULO: storage.py (Vector Store) (4)
===============================================================================
Definición:
-----------
Gestiona el almacenamiento y consulta de representaciones vectoriales de 
documentos usando ChromaDB.

Conceptos Clave:
----------------
- Vector Store: Base de datos optimizada para almacenar y buscar vectores.
- Embeddings: Representación numérica de un texto en un espacio semántico.
- Búsqueda Semántica: Recupera documentos por significado, no por coincidencia exacta de palabras.

Rol en el Sistema:
------------------
- Insertar (upsert) documentos con sus embeddings y metadata.
- Consultar los documentos más similares a una pregunta (query) usando embeddings.
===============================================================================
"""
# app/storage.py
# app/storage.py (fix de tipos para Chroma)
import os
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import time
from typing import Any, List, Dict

import chromadb


from app.logging_utils import logger, span
from app.deps import get_embedder

CHROMA_DIR = os.getenv("CHROMA_DIR", "data/chroma")
CHROMA_PERSIST = os.getenv("CHROMA_PERSIST", "1") not in ("0", "false", "False")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "elsol_conversations")
EMB_BATCH = int(os.getenv("EMB_BATCH", "32"))

_client: Any = None       
_collection: Any = None  

def _build_client() -> Any:   # ✅
    if CHROMA_PERSIST:
        logger.info(f"[DB] Chroma persistente en '{CHROMA_DIR}'")
        return chromadb.Client(chromadb.config.Settings(persist_directory=CHROMA_DIR))
    else:
        logger.info("[DB] Chroma en memoria (sin persistencia)")
        return chromadb.Client()

def get_collection() -> Any:  # ✅
    global _client, _collection
    if _client is None:
        with span("[DB] INIT CLIENT"):
            _client = _build_client()
    if _collection is None:
        with span("[DB] GET/CREATE COLLECTION"):
            _collection = _client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
    return _collection

def _encode_batch(texts: List[str]) -> List[List[float]]:
    emb = get_embedder()
    vecs = emb.encode(texts, normalize_embeddings=True)
    if not isinstance(vecs, list):
        vecs = vecs.tolist()
    return [v if isinstance(v, list) else v.tolist() for v in vecs]

def embed_texts(texts: List[str]) -> List[List[float]]:
    logger.info(f"[EMB] start batch={len(texts)} (EMB_BATCH={EMB_BATCH})")
    t0 = time.time()
    out: List[List[float]] = []
    for i in range(0, len(texts), EMB_BATCH):
        sl = texts[i : i + EMB_BATCH]
        with span(f"[EMB] ENCODE slice {i}-{i+len(sl)-1}"):
            vecs = _encode_batch(sl)
            out.extend(vecs)
    logger.info(f"[EMB] total encoded {len(out)} items in {time.time()-t0:.2f}s")
    return out

def upsert_documents(docs: List[Dict]) -> None:
    col = get_collection()
    ids = [d["id"] for d in docs]
    texts = [d["text"] for d in docs]
    metas = [d.get("metadata", {}) for d in docs]
    with span("[EMB] COMPUTE"):
        vecs = embed_texts(texts)
    with span("[DB] UPSERT"):
        col.upsert(ids=ids, documents=texts, embeddings=vecs, metadatas=metas)
        logger.info(f"[DB] upsert ok items={len(ids)}")

def query_similar(query: str, where: Dict | None = None, top_k: int = 6) -> List[Dict]:
    col = get_collection()
    with span("[EMB] QUERY EMBEDDING"):
        qvec = embed_texts([query])[0]
    
    with span("[DB] QUERY"):
        query_args = {
            "query_embeddings": [qvec],
            "n_results": top_k
        }
        if where:  # Solo agregar si hay algo válido
            query_args["where"] = where

        res = col.query(**query_args)
    
    out: List[Dict] = []
    if res and res.get("ids"):
        for i in range(len(res["ids"][0])):
            out.append({
                "id": res["ids"][0][i],
                "text": res["documents"][0][i],
                "metadata": res["metadatas"][0][i],
            })
    logger.info(f"[DB] query returned {len(out)} results")
    return out

def warmup_storage() -> None:
    with span("WARMUP: STORAGE"):
        get_collection()
        _ = embed_texts(["warmup"])
        logger.info("[WARMUP] storage ok")

def reset_db() -> None:
    if CHROMA_PERSIST:
        logger.info(f"[RESET] Eliminando {CHROMA_DIR} …")
        import shutil
        shutil.rmtree(CHROMA_DIR, ignore_errors=True)
        logger.info("[RESET] OK")
    else:
        logger.info("[RESET] En modo memoria: nada que borrar")