"""
===============================================================================
MÓDULO: deps.py (1)
===============================================================================
Definición:
-----------
Este módulo contiene funciones auxiliares y "dependencias" compartidas para 
otros componentes del sistema. Aquí centralizamos la inicialización de modelos 
y servicios que deben cargarse una sola vez (singleton/lazy loading).

Conceptos Clave:
----------------
- Singleton/Lazy Loading: Patrón donde un recurso pesado (modelo ML, 
  conexión) se inicializa una vez y se reutiliza.
- Embedder: Modelo de embeddings (vectorización) usado para convertir texto 
  en vectores numéricos para la búsqueda semántica.
- Variables de entorno (.env): Configuración sensible (API keys, endpoints) 
  que no debe quedar fija en el código.

Rol en el Sistema:
------------------
- Proveer el modelo de embeddings (`SentenceTransformer`) a otros módulos.
- Detectar si hay credenciales Azure configuradas para habilitar GPT-4.
===============================================================================
"""
import os
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from app.logging_utils import logger


@lru_cache(maxsize=1)
def get_embedder():
    # Modelo rápido y liviano (CPU OK)
    return SentenceTransformer("sentence-transformers/all-MiniLM-L12-v2")

def azure_enabled() -> bool:
    ep = os.getenv("AZURE_OPENAI_API_ENDPOINT")
    key = os.getenv("AZURE_OPENAI_API_KEY")
    dep = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    ok = bool(ep and key and dep)
    if not ok:
        logger.warning(f"[AZURE] Deshabilitado. endpoint={bool(ep)} api_key={bool(key)} deployment={bool(dep)}")
    return ok