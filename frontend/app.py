import os
import io
import json
import requests
import streamlit as st
from datetime import date

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="ElSol - RAG clínico", page_icon="🩺", layout="centered")

st.title("🩺 ElSol - RAG Clínico (Demo)")
st.caption(f"Backend: {BACKEND_URL}")

# --- Auth simple en sidebar ---
with st.sidebar:
    st.subheader("🔐 Autenticación")
    if "token" not in st.session_state:
        st.session_state.token = None
        st.session_state.role = None

    if st.session_state.token:
        st.success(f"Conectado ({st.session_state.role})")
        if st.button("Cerrar sesión"):
            st.session_state.token = None
            st.session_state.role = None
            st.rerun()
    else:
        u = st.text_input("Usuario", value="promotor")
        p = st.text_input("Contraseña", value="promotor123", type="password")
        if st.button("Iniciar sesión"):
            try:
                r = requests.post(f"{BACKEND_URL}/auth/login", json={"username": u, "password": p}, timeout=20)
                if r.ok:
                    data = r.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.role = data.get("role")
                    st.rerun()
                else:
                    st.error(r.text)
            except Exception as e:
                st.error(f"Error: {e}")

def auth_headers():
    if not st.session_state.token:
        return {}
    return {"Authorization": f"Bearer {st.session_state.token}"}

# Bloquea UI si no hay login
if not st.session_state.token:
    st.warning("Inicia sesión para usar la app.")
    st.stop()


tabs = st.tabs(["📤 Subir Audio", "📄 Subir PDF/Imagen", "💬 Chat"])

# --------------------------
# 📤 Subir Audio
# --------------------------
with tabs[0]:
    st.subheader("Subir audio (.mp3 / .wav)")
    audio_file = st.file_uploader("Selecciona un audio", type=["mp3", "wav"], key="audio_upl")

    if audio_file is not None:
        if st.button("Procesar audio"):
            files = {"file": (audio_file.name, audio_file.getvalue(), audio_file.type or "application/octet-stream")}
            try:
                with st.spinner("Subiendo y transcribiendo..."):
                    resp = requests.post(f"{BACKEND_URL}/upload_audio", files=files, headers=auth_headers(), timeout=120)
                if resp.ok:
                    st.success("✅ Audio procesado")
                    st.json(resp.json())
                else:
                    st.error(f"❌ Error {resp.status_code}")
                    st.code(resp.text)
            except Exception as e:
                st.error(f"❌ Error al llamar backend: {e}")

# --------------------------
# 📄 Subir PDF / Imagen
# --------------------------
with tabs[1]:
    st.subheader("Subir documento (PDF / imagen)")
    doc_file = st.file_uploader("Selecciona un PDF/imagen", type=["pdf", "png", "jpg", "jpeg", "webp"], key="doc_upl")

    if doc_file is not None:
        if st.button("Procesar documento"):
            files = {"file": (doc_file.name, doc_file.getvalue(), doc_file.type or "application/octet-stream")}
            try:
                with st.spinner("Subiendo y extrayendo texto..."):
                    resp = requests.post(f"{BACKEND_URL}/upload_doc", files=files, headers=auth_headers(), timeout=180)
                if resp.ok:
                    st.success("✅ Documento procesado")
                    st.json(resp.json())
                else:
                    st.error(f"❌ Error {resp.status_code}")
                    st.code(resp.text)
            except Exception as e:
                st.error(f"❌ Error al llamar backend: {e}")

# --------------------------
# 💬 Chat
# --------------------------
with tabs[2]:
    st.subheader("Chat con RAG")
    q = st.text_area("Tu pregunta", placeholder="¿Cuáles fueron las observaciones hechas al paciente Juan Pérez?", height=120)

    with st.expander("Filtros (opcional)"):
        col1, col2 = st.columns(2)
        patient_name = col1.text_input("Nombre del paciente", value="")
        use_date = col2.checkbox("Filtrar por rango de fechas", value=False)
        since, until = None, None
        if use_date:
            col3, col4 = st.columns(2)
            since = col3.date_input("Desde", value=date(2025, 7, 1))
            until = col4.date_input("Hasta", value=date(2025, 7, 31))
        use_age = st.checkbox("Filtrar por edad (rango)", value=False)
        min_age, max_age = None, None
        if use_age:
            col5, col6 = st.columns(2)
            min_age = col5.number_input("Edad mínima", min_value=0, max_value=120, value=18)
            max_age = col6.number_input("Edad máxima", min_value=0, max_value=120, value=65)

    if st.button("Preguntar"):
        if not q.strip():
            st.warning("Escribe una pregunta.")
        else:
            payload = {"query": q, "filters": {}}

            # paciente
            if patient_name.strip():
                payload["filters"]["patient_name"] = patient_name.strip()

            # fechas
            if use_date and since and until and since <= until:
                payload["filters"]["date_range"] = [since.strftime("%Y-%m-%d"), until.strftime("%Y-%m-%d")]

            # edad
            if use_age and min_age is not None and max_age is not None and min_age <= max_age:
                payload["filters"]["age"] = {"$gte": int(min_age), "$lte": int(max_age)}

            try:
                with st.spinner("Consultando..."):
                    resp = requests.post(f"{BACKEND_URL}/chat", json=payload, headers=auth_headers(), timeout=120)
                if resp.ok:
                    data = resp.json()
                    st.markdown("### 🧠 Respuesta")
                    st.write(data.get("answer", ""))

                    cits = data.get("citations", [])
                    if isinstance(cits, list) and cits:
                        st.markdown("**Citas (source_id):**")
                        st.code("\n".join(cits))
                else:
                    st.error(f"❌ Error {resp.status_code}")
                    st.code(resp.text)
            except Exception as e:
                st.error(f"❌ Error al llamar backend: {e}")