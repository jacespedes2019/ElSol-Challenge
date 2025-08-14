"""
===============================================================================
MÓDULO: models.py (7)
===============================================================================
Definición:
-----------
Contiene los modelos de datos (Pydantic) usados para validar y documentar 
las entradas y salidas de la API.

Conceptos Clave:
----------------
- Pydantic: Librería que valida datos basados en modelos tipados y 
  genera documentación automática para FastAPI.
- DTO (Data Transfer Object): Estructuras que transportan datos entre 
  capas del sistema.
- response_model: Parámetro de FastAPI para validar y documentar 
  automáticamente las respuestas.

Rol en el Sistema:
------------------
- Estandarizar el formato de datos de entrada y salida.
- Garantizar consistencia y detección temprana de errores de formato.
===============================================================================
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from typing import Any, Dict, Optional, List

class UploadResponse(BaseModel):
    ok: bool
    source_id: str
    chunks_indexed: int

class ChatQuery(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        example = {
        "$and": [
        {"patient_name": {"$eq": "Juan Pérez"}},
        {"date": {"$gte": "2025-07-01", "$lte": "2025-07-31"}},
        {"age": {"$gte": 18, "$lte": 65}}
          ]
      }
    )

class ChatResponse(BaseModel):
    answer: str
    citations: List[str]
    
class LoginBody(BaseModel):
    username: str
    password: str
