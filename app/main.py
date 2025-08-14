"""
===============================================================================
MÓDULO: main.py (FastAPI Entrypoint) (8)
===============================================================================
Definición:
-----------
Punto de entrada de la aplicación FastAPI. Define los endpoints principales 
y conecta todas las piezas del sistema.

Conceptos Clave:
----------------
- Endpoint: Ruta HTTP que expone una funcionalidad (POST, GET, etc.).
- CORS Middleware: Configuración que permite llamadas a la API desde 
  diferentes orígenes (dominios).
- /upload_audio: Recibe un audio, lo transcribe, extrae datos y lo indexa.
- /chat: Responde preguntas consultando la base vectorial y usando el LLM.

Rol en el Sistema:
------------------
- Coordinar el flujo: recibir datos → procesar → indexar → responder.
- Proveer la interfaz HTTP que usará el cliente (frontend, Postman, cURL).
===============================================================================
"""
import os, time
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.asr import transcribe_audio, get_asr
from app.extract import extract_structured, naive_extract
from app.ocr import extract_text_from_file
from app.rag import index_transcript, retrieve_chunks
from app.llm import chat_completion
from app.models import UploadResponse, ChatQuery, ChatResponse
from app.logging_utils import span, logger
from app.deps import get_embedder
from app.storage import embed_texts, get_collection
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="ElSol Challenge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)


@app.on_event("startup")
def warmup():
    with span("WARMUP: ASR/EMB/DB"):
        # 1) Carga modelos
        get_asr()
        emb = get_embedder()

        # 2) Fuerza un encode (descarga + compilación + tokenizers)
        _ = emb.encode(["warmup"], normalize_embeddings=True)

        # 3) Inicializa Chroma y hace “ping”
        col = get_collection()
        try:
            col.count()  # si tu versión no lo expone, omite esto
        except Exception:
            pass

        # 4) Calienta el pipeline de embeddings usado por storage
        _ = embed_texts(["warmup"])

        logger.info("[WARMUP] listo")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload_audio", response_model=UploadResponse)
async def upload_audio(file: UploadFile = File(...)):
    try:
        os.makedirs("data/uploads", exist_ok=True)
        path = f"data/uploads/{file.filename}"

        with span("SAVE FILE"):
            size = 0
            with open(path, "wb") as f:
                while True:
                    chunk = await file.read(1024 * 1024)  # 1MB
                    if not chunk:
                        break
                    size += len(chunk)
                    f.write(chunk)
            logger.info(f"[FILE] Guardado {path} ({size/1e6:.2f} MB)")

        with span("ASR: TRANSCRIBE"):
            transcript = transcribe_audio(path)
            logger.info(f"[ASR] Transcript len={len(transcript)} chars")

        with span("EXTRACT: STRUCTURED FIELDS"):
            info = extract_structured(transcript)
            patient = info.patient_name or "desconocido"
            date = info.date
            age = info.age
            logger.info(f"[EXTRACT] patient={patient} date={date} age={age} symptoms={len(info.symptoms)}")

        with span("INDEX: EMBEDDINGS + UPSERT"):
            result = index_transcript(
                transcript=transcript,
                patient_name=patient,
                date_str=date,
                age=age,
                source_id=None
            )

        logger.info("[PIPELINE] COMPLETADO")
        return {"ok": True, "source_id": result["source_id"], "chunks_indexed": result["chunks_indexed"]}

    except Exception as e:
        logger.exception("❌ Error en /upload_audio")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(query: ChatQuery):
    try:
        with span("RAG: RETRIEVE"):
            chunks = retrieve_chunks(query.query, filters=query.filters)
        
        # Construimos el prompt con contexto RAG
        context_text = "\n\n".join([c["text"] for c in chunks])
        messages = [
            {"role": "system", "content": "Eres un asistente médico que responde basándose SOLO en la información provista."},
            {"role": "user", "content": f"Pregunta: {query.query}\n\nContexto:\n{context_text}"}
        ]
        
        with span("LLM: ANSWER"):
         answer = chat_completion(messages)

        # solo source_ids únicos y no nulos
        cit_ids = list({c["source_id"] for c in chunks if c.get("source_id")})

        return {
            "answer": answer,
            "citations": cit_ids
        }
    except Exception as e:
        logger.exception("❌ Error en /chat")
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/upload_doc", response_model=UploadResponse)
async def upload_doc(file: UploadFile = File(...)):
    """
    Sube un PDF o imagen, extrae el texto (OCR si hace falta), lo “extrae” (structured/unstructured)
    y lo indexa igual que el audio.
    """
    try:
        os.makedirs("data/docs", exist_ok=True)
        path = f"data/docs/{file.filename}"

        with span("SAVE FILE (DOC)"):
            size = 0
            with open(path, "wb") as f:
                while True:
                    chunk = await file.read(1024 * 1024)  # 1MB
                    if not chunk:
                        break
                    size += len(chunk)
                    f.write(chunk)
            logger.info(f"[FILE] Guardado {path} ({size/1e6:.2f} MB)")

        with span("DOC: EXTRACT TEXT (OCR/PDF)"):
            text, kind = extract_text_from_file(path, file.content_type)
            logger.info(f"[DOC] kind={kind} chars={len(text)}")

            if not text or len(text.strip()) < 5:
                raise HTTPException(status_code=400, detail="No se pudo extraer texto del documento.")

        with span("EXTRACT: STRUCTURED FIELDS (DOC)"):
            info = extract_structured(text)  # usa mismo extractor que audio
            patient = (getattr(info, "structured", None) or getattr(info, "patient_name", None))
            # compat: si usas ClinicalExtract, viene dentro de info.structured
            if hasattr(info, "structured"):
                s = info.structured
                patient_name = s.patient_name or "desconocido"
                date = s.date
                age = s.age if hasattr(s, "age") else None
            else:
                # si conservaste el PatientInfo anterior
                patient_name = info.patient_name or "desconocido"
                date = info.date
                age = getattr(info, "age", None)

            logger.info(f"[EXTRACT/DOC] patient={patient_name} date={date} age={age}")

        with span("INDEX: EMBEDDINGS + UPSERT (DOC)"):
            result = index_transcript(
                transcript=text,
                patient_name=patient_name,
                date_str=date,
                age=age,
                source_id=None
            )

        logger.info("[PIPELINE/DOC] COMPLETADO")
        return {"ok": True, "source_id": result["source_id"], "chunks_indexed": result["chunks_indexed"]}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("❌ Error en /upload_doc")
        raise HTTPException(status_code=500, detail=str(e))