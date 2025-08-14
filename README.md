# ✅ ElSol-Challenge


---

## 📣 Requerimiento del Cliente

> “Queremos ser capaces de grabar conversaciones entre nuestro personal promotor y posibles pacientes.  
> Luego, queremos hacerle preguntas a un chatbot como:  
> - ¿Qué síntomas tiene Juan Pérez?  
> - ¿Qué pacientes reportaron fiebre en julio?  
> - Créame un Plan de cuidado para Juan Pérez.  
>   
> También queremos que en el futuro se puedan subir documentos (como exámenes en PDF o fotos de heridas) asociados a cada paciente.  
>   
> Lo más importante para nosotros es que la información quede organizada, sea fácil de consultar, segura, y que el sistema sea escalable.”

---

## 💡 Consideraciones

- Puedes asumir lo que necesites para resolver la prueba (formatos, flujos, bases de datos, etc.), pero debes documentar claramente tus decisiones y supuestos.
- Se recomienda usar Python + FastAPI, pero puedes estructurar el proyecto como desees.
- La parte de frontend es opcional.
- Si no alcanzas a terminar todo, lo importante es la documentación técnica y el razonamiento detrás de tu solución.

---

## 📦 Entregables esperados

### 📁 1. Repositorio en GitHub

- Código limpio, modular y documentado.
- Este README debe incluir:
  - ✅ Instrucciones para correr el proyecto
  - ✅ Descripción de los endpoints disponibles
  - ✅ Cómo testear la funcionalidad
  - ✅ Supuestos hechos
  - ✅ Buenas prácticas aplicadas

### 📄 2. Documento Técnico (PDF o Markdown)

Debe incluir:

#### A. 📍 Análisis del requerimiento
- ¿Qué funcionalidades propusiste?
- ¿Qué decisiones técnicas tomaste y por qué?
- ¿Qué supuestos hiciste?

#### B. 🏗️ Arquitectura propuesta
- Diagrama del sistema
- Componentes del backend y flujo de datos
- Justificación de tecnologías y herramientas

#### C. 🚀 Plan de desarrollo
- ¿Qué hiciste en esta entrega (MVP)?
- ¿Qué funcionalidades PLUS desarrollaste?
- ¿Qué implementarías como siguientes pasos?
- ¿Cómo llevarías este sistema a producción? (infraestructura, seguridad, MLOps, cloud)

---

## 📌 Requisitos Mínimos (Obligatorios)

### 🎙️ 1. Transcripción de Audio

- Permitir subir archivos `.wav` o `.mp3`.
- Transcribir conversaciones utilizando alguna de las siguientes (u otra justificada):
  - OpenAI Whisper (API o local)
  - Azure Speech to Text
  - Google Speech to Text
  - Cualquier API o librería open source
- ⚠️ Justifica por qué elegiste esa herramienta y cuál sería ideal para producción.
- Extraer:
  - Información estructurada (nombre, edad, diagnóstico, fecha, etc.)
  - Información no estructurada (síntomas, contexto conversacional, observaciones)

---

### 🧠 2. Almacenamiento Vectorial

- Almacenar la información procesada en una base vectorial, como:
  - Qdrant
  - pgvector
  - Chroma
  - Milvus
  - Otra (con justificación)

---

### 💬 3. Chatbot vía API

- Implementar un endpoint `/chat` que permita hacer preguntas como:
  - “¿Qué enfermedad tiene Pepito Gómez?”
  - “Listame los pacientes con diabetes”
- Utilizar un LLM (ej: OpenAI GPT-4 vía Azure) para generar respuestas a partir de los datos vectorizados.

---

## 🌟 PLUS (Opcionales – Suman puntos)

- 🟢 Transcripción en tiempo real (streaming o chunked).
- 🟢 Cliente simple (ej: React) para subir audio y consultar al chatbot.
- 🟢 Subida de PDFs o imágenes asociadas al paciente (con OCR/parsing).
- 🟢 Diferenciación de hablantes (paciente vs promotor).
- 🟢 Buenas prácticas de MLOps (pipelines, versionado, tests).
- 🟢 Seguridad: autenticación, protección de endpoints, cifrado, control de acceso.

---

## ⏳ Tiempo estimado

- Esta prueba está diseñada para completarse en un máximo de 2 días efectivos (~16 horas).
- No necesitas terminar todo, pero debes documentar claramente:
  - Qué entregaste.
  - Qué decidiste no implementar.
  - Qué harías como siguiente paso.

---

## 🧠 Criterios de Evaluación

| Criterio                                | Peso |
|-----------------------------------------|------|
| Entendimiento del requerimiento         | 5%   |
| Correctitud y funcionalidad mínima      | 40%  |
| Claridad del código y documentación     | 10%  |
| Calidad del documento técnico (PDF)     | 25%  |
| Plan de producción y escalabilidad      | 10%  |
| PLUS y creatividad en la solución       | 10%  |

---

## 🔐 Recursos disponibles

- Se te proporcionará una API Key de Azure OpenAI si deseas usar GPT-4 para el chatbot.
- Puedes utilizar cualquier motor de transcripción o LLM, mientras expliques y justifiques bien tu decisión.

---

## 📨 ¿Cómo entregar?

1. Haz un fork privado de este repositorio.
2. Agrega como colaborador a `David-Sol-AI`.
3. Sube tu solución al repositorio.
4. Agrega tu documento técnico (`documentacion.pdf` o `documentacion.md`) en la raíz.
5. Envía un correo a `projectmanagerengineer@elsolnec.org` con el enlace a tu repositorio y cualquier comentario adicional.

---

¡Mucho éxito! 🚀
