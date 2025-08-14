# Usa imagen multi-arch (sirve en Intel y Apple Silicon)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ---- Dependencias del sistema ----
# - ffmpeg: para manejo de audio (ASR)
# - poppler-utils: pdf -> imagen (para OCR de PDFs escaneados)
# - libgl1, libglib2.0-0: para PIL / pdf2image / EasyOCR
# - build-essential: compilar deps nativos si hace falta
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Directorio de la app
WORKDIR /app

# Copiamos requirements primero (para cache de pip)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiamos el resto del proyecto
COPY . /app

# Variables por defecto (puedes sobreescribir con .env / docker-compose)
ENV CHROMA_DIR=/app/data/chroma \
    CHROMA_PERSIST=1 \
    CHROMA_COLLECTION=elsol_conversations

# Expone FastAPI
EXPOSE 8000

# Arranque
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]