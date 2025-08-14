"""
===============================================================================
MÓDULO: llm.py (Large Language Model) (3)
===============================================================================
Definición:
-----------
Un LLM es un modelo de lenguaje entrenado para comprender y generar texto. 
Este módulo gestiona la conexión con Azure OpenAI GPT-4/4o para generar 
respuestas a partir de contexto recuperado (RAG).

Conceptos Clave:
----------------
- GPT-4/GPT-4o: Modelos de OpenAI disponibles en Azure para tareas de 
  comprensión, razonamiento y generación de texto.
- Deployment: En Azure, un deployment es una instancia específica de un 
  modelo con un nombre asignado (no confundir con el nombre del modelo).
- Chat Completion API: Endpoint que recibe una lista de mensajes 
  (system/user/assistant) y devuelve texto generado.

Rol en el Sistema:
------------------
- Proveer una función `chat_completion` que encapsula la llamada a Azure GPT.
- Manejar fallback local cuando Azure no está configurado.
===============================================================================
"""
import os
from typing import List, Dict
from openai import AzureOpenAI
from app.deps import azure_enabled

_client = None
_deployment = None

def get_llm_client():
    global _client, _deployment
    if not azure_enabled():
        return None, None
    if _client is None:
        _client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_API_ENDPOINT"),
        )
        _deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    return _client, _deployment

def chat_completion(messages: List[Dict], temperature: float = 0.2, max_tokens: int = 500) -> str:
    client, deployment = get_llm_client()
    if client is None:
        # Fallback: une contexto y devuelve eco (útil para debug sin Azure)
        user = next((m["content"] for m in messages[::-1] if m["role"]=="user"), "")
        return f"[MODO LOCAL] Sin Azure configurado. Pregunta recibida: {user[:300]}..."
    resp = client.chat.completions.create(
        model=deployment,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content