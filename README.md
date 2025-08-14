# 🩺 ElSol - RAG Clínico (Prueba Técnica)

Este proyecto implementa un sistema de **transcripción de audio**, **extracción de información clínica** y **búsqueda conversacional** usando un backend en **FastAPI** y un frontend en **Streamlit**.

Por Jairo Adolfo Céspedes Plata

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
#### Es indispensable pararse en la raíz del proyecto 
	cd ElSol-Challenge 

### 2. Crear archivo .env

El contenido del archivo .env será enviado adjunto en el correo de respuesta.
Este contiene las claves y configuraciones necesarias.

⸻

### 3. Construir y levantar el backend y frontend con Docker

#### Precaución: En Windows el build debido a las librerías puede demorarse hasta 10 min o un poco más, en Mac si es más rápido

	docker-compose up --build

Esperar a que salga el siguiente mensaje: 

<img width="1180" height="138" alt="image" src="https://github.com/user-attachments/assets/dfe23a76-6847-4a81-9256-48dfc1f93452" />


Esto arrancará el backend en http://localhost:8000 y su documentación en http://localhost:8000/docs

El frontend estará disponible en http://localhost:8501

⸻

### 🔑 Credenciales de prueba (Base de datos dummy)

Se incluye un sistema básico de autenticación JWT con usuarios simulados.
Todos los passwords ya están hasheados internamente.

|Usuario	|Rol	|Contraseña|
|----------|----------|----------|
|promotor	|promotor	|promotor123|
|medico	|medico	|medico123|
|admin	|admin	|admin123|


⸻

### Cómo testear la funcionalidad (desde el frontend)
1.	Acceder al frontend
   
Ir a http://localhost:8501 en tu navegador.

2.	Iniciar sesión

•	En la pantalla inicial, ingresar un usuario y contraseña de la tabla de credenciales.

•	Ejemplo: Usuario: promotor Contraseña: promotor123

•	Presionar Login.

•	Si las credenciales son correctas, se almacenará el token JWT para las siguientes acciones.

3.	Subir un archivo de audio para transcripción

•	Ir a la sección “Subir Audio”.

•	Seleccionar un archivo .wav o .mp3.

•	Presionar Procesar Audio.

•	El sistema transcribirá el contenido y lo indexará en la base vectorial.

4.	Subir un documento PDF o imagen para OCR

•	Ir a la sección “Subir Documento”.

•	Seleccionar un PDF o imagen (JPG, PNG).

•	Presionar Procesar Documento.

•	El texto detectado se guardará junto con los metadatos del paciente.

5.	Realizar una consulta al chatbot
	
 •	Ir a la sección “Consulta”.

•	Escribir una pregunta como: ¿Qué diagnóstico tiene Juan Pérez?
	
 •	(Opcional) Aplicar filtros de fecha, edad o nombre.
	
 •	Presionar Enviar Pregunta.
	
 •	El chatbot devolverá la respuesta junto con las citas de los documentos relevantes.

	
 6.	Ver resultados
	
 •	En cada sección, el frontend mostrará mensajes de éxito o error.
	
 •	En el chat, se mostrarán también los IDs de las fuentes para trazabilidad.

### 📌 Ejemplos de uso de la API

### Descripción de los endpoints disponibles
	•	POST /login → Autenticación de usuario y obtención de token JWT.
	•	POST /upload_audio → Sube un archivo de audio (.wav, .mp3) y realiza transcripción + extracción de información.
	•	POST /upload_doc → Sube un PDF o imagen y extrae texto vía OCR.
	•	POST /chat → Permite realizar consultas en lenguaje natural sobre la información almacenada.
	•	GET /docs → Documentación Swagger del backend.
	•	GET /redoc → Documentación ReDoc del backend.


#### 1. Autenticación y obtención de token

	curl -X POST http://localhost:8000/login \
	-H "Content-Type: application/json" \
	-d '{"username": "promotor", "password": "promotor123"}'

Respuesta:

	{
	  "access_token": "JWT_GENERADO",
	  "token_type": "bearer"
	}


⸻

#### 2. Subir Audio

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

#### 3. Subir Documento (PDF/Imagen)

	curl -X POST http://localhost:8000/upload_doc \
	-H "Authorization: Bearer JWT_GENERADO" \
	-F "file=@muestra.pdf"


⸻

#### 4. Consultar Chat

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

### Supuestos realizados
	•	Los nombres de pacientes pueden venir tanto en audio como en los documentos; si no aparece, se etiqueta como “desconocido”.
	•	La fecha se normaliza a YYYY-MM-DD cuando se identifica en el texto; de lo contrario, se usa la fecha actual al indexar.
	•	La metadata mínima para búsquedas incluye: source_id, patient_name, date y age.
	•	El LLM no debe inventar datos; se guía con prompts restrictivos y RAG. Aun así, se devuelve contexto y citas.
	•	El almacenamiento de usuarios es de demostración (dummy); se asume que en producción se integrará un IAM real.
	•	Se asume que todo lo que entra para el mismo nombre es el mismo usuario.

### Buenas prácticas aplicadas
	•	Dockerización del backend y frontend para ejecución consistente.
	•	Autenticación JWT con control de roles (promotor, medico, admin).
	•	Cifrado de contraseñas con bcrypt.
	•	Arquitectura modular en FastAPI con separación por responsabilidades.
	•	Uso de embeddings semánticos propios para mejorar la búsqueda contextual.
	•	Validación de inputs y control de errores.
	•	Documentación automática de endpoints vía Swagger y ReDoc.
	•	Compatibilidad multi-arch en el Dockerfile para correr en Intel y ARM (Apple Silicon).


### 📂 Estructura del proyecto
<img width="496" height="1274" alt="image" src="https://github.com/user-attachments/assets/5e994e31-33aa-4689-ab09-7e1882171861" />

⸻

### 📚 Notas finales
	•	La documentación técnica completa está documentacion.pdf.
	•	Este sistema usa embeddings propios generados con SentenceTransformer("sentence-transformers/all-MiniLM-L12-v2") para mejorar la búsqueda semántica.
	•	El backend está protegido con autenticación JWT y control de roles.
	•	La base de datos de usuarios es dummy pero ya maneja hash de contraseñas y tokenización.

⸻
