FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ---- Dependencias del sistema ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiamos primero requirements para cachear la instalación
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# Ahora copiamos el resto del proyecto
COPY . /app

ENV CHROMA_DIR=/app/data/chroma \
    CHROMA_PERSIST=1 \
    CHROMA_COLLECTION=elsol_conversations

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]