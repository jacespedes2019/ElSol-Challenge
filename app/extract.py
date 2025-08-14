"""
===============================================================================
MÓDULO: extract.py (6)
===============================================================================
Definición:
-----------
Extrae información estructurada (nombre, edad, fecha, síntomas) desde texto
libre. Intenta primero con LLM (Azure OpenAI) y, si falla o no está habilitado,
usa un extractor naive por regex.

Conceptos Clave:
----------------
- Extracción Estructurada con LLM: Se le pide al modelo que devuelva JSON
  estricto con un esquema fijo (validado luego con Pydantic).
- Fallback: Si el LLM no está disponible o devuelve algo no parseable,
  se recurre a regex simples para no bloquear el flujo.

Rol en el Sistema:
------------------
- Convertir la transcripción en campos que luego se guardan como metadata y
  permiten filtros en el vector store (búsqueda por paciente, fecha, etc.).
===============================================================================
"""
from __future__ import annotations

import json
import re
from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError

# LLM (Azure/OpenAI). Usa el helper que ya tienes en app/llm.py
from app.llm import chat_completion
from app.deps import azure_enabled
from app.logging_utils import span, logger


# -----------------------------
# Esquema Pydantic
# -----------------------------
class PatientInfo(BaseModel):
    patient_name: Optional[str] = Field(default=None, description="Nombre completo del paciente")
    age: Optional[int] = Field(default=None, description="Edad entera si está disponible")
    date: Optional[str] = Field(default=None, description="Fecha en formato YYYY-MM-DD si está en el texto")
    symptoms: List[str] = Field(default_factory=list, description="Lista de síntomas detectados")


# -----------------------------
# Regex fallback (naive)
# -----------------------------
NAME_PAT = re.compile(r"(paciente|nombre)\s*[:\-]\s*([A-ZÁÉÍÓÚÑa-záéíóúñ ]{3,})")
AGE_PAT  = re.compile(r"(edad)\s*[:\-]\s*(\d{1,3})")
DATE_PAT = re.compile(r"(fecha)\s*[:\-]\s*(\d{4}-\d{2}-\d{2})")

# Puedes ampliar esta lista o moverla a config
SYMPTOMS_LEXICON = [
    "fiebre", "tos", "dolor de cabeza", "dolor de garganta", "dolor muscular",
    "fatiga", "náusea", "nausea", "vómito", "vomito", "diarrea",
    "dificultad para respirar", "disnea", "congestión", "congestion"
]


def naive_extract(text: str) -> PatientInfo:
    t = text.strip()
    tl = t.lower()

    name = None
    age = None
    date = None

    m = NAME_PAT.search(tl)
    if m:
        name = m.group(2).strip()
        # Normaliza capitalización
        name = " ".join(w.capitalize() for w in name.split())

    m = AGE_PAT.search(tl)
    if m:
        try:
            age = int(m.group(2))
        except Exception:
            age = None

    m = DATE_PAT.search(tl)
    if m:
        date = m.group(2)

    syms = []
    for s in SYMPTOMS_LEXICON:
        if s in tl:
            syms.append(s)

    # Quita duplicados preservando orden
    seen = set()
    symptoms = []
    for s in syms:
        if s not in seen:
            symptoms.append(s)
            seen.add(s)

    return PatientInfo(patient_name=name or None, age=age, date=date, symptoms=symptoms)


# -----------------------------
# LLM extraction (Azure/OpenAI)
# -----------------------------
_SYSTEM_PROMPT = (
    "Eres un sistema de extracción clínica en español. "
    "Debes devolver EXCLUSIVAMENTE un objeto JSON válido con las claves:\n"
    "  - patient_name (string o null)\n"
    "  - age (entero o null)\n"
    "  - date (string YYYY-MM-DD o null)\n"
    "  - symptoms (array de strings, puede ser vacía)\n\n"
    "Reglas:\n"
    "- No inventes datos. Si no están en el texto, usa null o [].\n"
    "- Si hay varios posibles nombres, elige el más probable del paciente.\n"
    "- Para la fecha, usa formato YYYY-MM-DD si aparece; si no, null.\n"
    "- Para síntomas, devuelve palabras/frases clínicas breves en minúsculas.\n"
    "- Responde SOLO el JSON sin comentarios, sin texto adicional."
)

_USER_TEMPLATE = (
    "Texto de entrada (transcripción):\n"
    "-------------------------------\n"
    "{transcript}\n"
    "-------------------------------\n"
    "Devuelve el JSON con el esquema indicado."
)


def _parse_llm_json(text: str) -> dict:
    """
    Intenta parsear JSON de forma robusta:
    - Primero intenta json.loads directo.
    - Si falla, intenta recortar desde el primer '{' hasta el último '}'.
    """
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = text[start:end+1]
            return json.loads(snippet)
        raise


def azure_llm_extract(text: str) -> PatientInfo:
    """
    Pide al LLM que devuelva JSON con el esquema.
    Luego valida con Pydantic y normaliza algunos campos.
    """
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": _USER_TEMPLATE.format(transcript=text)},
    ]

    # Temperatura 0 para extracción determinista
    raw = chat_completion(messages, temperature=0, max_tokens=300)

    data = _parse_llm_json(raw)
    info = PatientInfo.model_validate(data)

    # Normalizaciones ligeras
    if info.patient_name:
        info.patient_name = " ".join(w.capitalize() for w in info.patient_name.split())

    if info.symptoms:
        # Limpiamos y normalizamos a minúsculas, sin duplicados
        norm = []
        seen = set()
        for s in info.symptoms:
            if not isinstance(s, str):
                continue
            ss = s.strip().lower()
            if ss and ss not in seen:
                norm.append(ss)
                seen.add(ss)
        info.symptoms = norm

    return info


# -----------------------------
# Interfaz pública
# -----------------------------
def extract_structured(text: str) -> PatientInfo:
    if not text or not text.strip():
        return PatientInfo()
    if azure_enabled():
        try:
            logger.info("[EXTRACT] Intentando LLM (Azure)")
            return azure_llm_extract(text)
        except Exception as e:
            logger.exception(f"[EXTRACT] LLM falló, usando fallback. Motivo: {e}")
    else:
        logger.info("[EXTRACT] Azure no habilitado, usando fallback")
    return naive_extract(text)