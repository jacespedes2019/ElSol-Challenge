"""
===============================================================================
MÓDULO: asr.py (Automatic Speech Recognition) (2)
===============================================================================
Definición:
-----------
ASR (Reconocimiento Automático de Voz) es el proceso de convertir audio 
(habla) en texto escrito. Este módulo implementa la transcripción local 
usando faster-whisper.

Conceptos Clave:
----------------
- Whisper: Modelo de ASR de OpenAI, entrenado para múltiples idiomas y 
  robusto a ruido. `faster-whisper` es una implementación optimizada.
- VAD (Voice Activity Detection): Filtra segmentos sin voz para mejorar 
  la precisión y reducir el tiempo de procesamiento.
- Modelo Base: "base", "small", "medium", "large" definen el tamaño y 
  precisión del modelo (mayor tamaño = más precisión, pero más lento).

Rol en el Sistema:
------------------
- Procesar archivos `.wav` o `.mp3` para obtener texto bruto.
- Paso inicial para extraer información clínica y permitir la indexación.
===============================================================================
"""
from faster_whisper import WhisperModel

# Carga perezosa (evita cargar el modelo si no se usa)
_model = None

def get_asr():
    global _model
    if _model is None:
        _model = WhisperModel("base", device="auto", compute_type="int8")
    return _model

def transcribe_audio(path: str) -> str:
    model = get_asr()
    segments, info = model.transcribe(path, vad_filter=True)
    text_parts = []
    for seg in segments:
        text_parts.append(seg.text.strip())
    return " ".join(text_parts)