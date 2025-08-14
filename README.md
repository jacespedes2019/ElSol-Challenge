# 🩺 ElSol - RAG Clínico (Prueba Técnica)

Este proyecto implementa un sistema de **transcripción de audio**, **extracción de información clínica** y **búsqueda conversacional** usando un backend en **FastAPI** y un frontend en **Streamlit**.

La documentación interactiva del backend está disponible en:
- **Swagger UI:** `http://localhost:8000/docs`

---

## 📦 Requisitos Previos

Asegúrate de tener instalado:

- **Docker** y **Docker Compose**
- **Git**

---

## 🚀 Ejecución del Proyecto

### 1. Clonar el repositorio
git clone https://github.com/jacespedes2019/ElSol-Challenge.git

## cd ElSol-Challenge (es indispensable pararse en la raíz del proyecto)

### 2. Crear archivo .env

El archivo .env será enviado adjunto en el correo de respuesta.
Este contiene las claves y configuraciones necesarias.

⸻

### 3. Construir y levantar el backend y frontend con Docker

docker-compose up --build

Esperar a que salga el siguiente mensaje: 

<img width="1180" height="138" alt="image" src="https://github.com/user-attachments/assets/dfe23a76-6847-4a81-9256-48dfc1f93452" />


Esto arrancará el backend en http://localhost:8000 y su documentación en http://localhost:8000/docs

El frontend estará disponible en http://localhost:8501

⸻

### 🔑 Credenciales de prueba (Base de datos dummy)

Se incluye un sistema básico de autenticación JWT con usuarios simulados.
Todos los passwords ya están hasheados internamente.

Usuario	Rol	Contraseña
promotor	promotor	promotor123
medico	medico	medico123
admin	admin	admin123


⸻

### 📌 Ejemplos de uso de la API

### 1. Autenticación y obtención de token

curl -X POST http://localhost:8000/login \
-H "Content-Type: application/json" \
-d '{"username": "promotor", "password": "promotor123"}'

Respuesta:

{
  "access_token": "JWT_GENERADO",
  "token_type": "bearer"
}


⸻

### 2. Subir Audio

curl -X POST http://localhost:8000/upload_audio \
-H "Authorization: Bearer JWT_GENERADO" \
-F "file=@muestra.wav"

Respuesta:

{
  "ok": true,
  "source_id": "abc123",
  "chunks_indexed": 8
}


⸻

### 3. Subir Documento (PDF/Imagen)

curl -X POST http://localhost:8000/upload_doc \
-H "Authorization: Bearer JWT_GENERADO" \
-F "file=@muestra.pdf"


⸻

4. Consultar Chat

curl -X POST http://localhost:8000/chat \
-H "Authorization: Bearer JWT_GENERADO" \
-H "Content-Type: application/json" \
-d '{
  "query": "¿Qué diagnóstico tiene Juan Pérez?",
  "filters": {
    "$and": [
      {
        "patient_name": {
          "$eq": "Juan Pérez"
        }
      },
      {
        "date": {
          "$gte": "2025-07-01",
          "$lte": "2025-07-31"
        }
      },
      {
        "age": {
          "$gte": 18,
          "$lte": 65
        }
      }
    ]
  }
}

Respuesta:

{
  "answer": "El paciente presenta síntomas compatibles con...",
  "citations": ["abc123"]
}


⸻

### 📂 Estructura del proyecto
<img width="496" height="1274" alt="image" src="https://github.com/user-attachments/assets/5e994e31-33aa-4689-ab09-7e1882171861" />

⸻

### 📚 Notas finales
	•	La documentación técnica completa está documentacion.pdf.
	•	Este sistema usa embeddings propios generados con SentenceTransformer("sentence-transformers/all-MiniLM-L12-v2") para mejorar la búsqueda semántica.
	•	El backend está protegido con autenticación JWT y control de roles.
	•	La base de datos de usuarios es dummy pero ya maneja hash de contraseñas y tokenización.

⸻
