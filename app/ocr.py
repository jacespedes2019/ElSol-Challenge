# app/ocr.py
"""
OCR utilitario para PDF e imágenes usando EasyOCR:
- PDF: intenta extraer texto con pdfplumber (texto embebido).
       Si no hay, OCR página a página con pdf2image + EasyOCR.
- Imágenes (png/jpg/jpeg/webp): OCR con EasyOCR directamente.

Notas:
- Carga el modelo EasyOCR 1 sola vez (LRU cache) para evitar latencias repetidas.
- Idiomas: prioriza español ('es') con apoyo en inglés ('en').
"""
from __future__ import annotations
import os
from typing import Tuple, Optional, List

import numpy as np
from PIL import Image
import pdfplumber
from pdf2image import convert_from_path
import easyocr
from functools import lru_cache

from app.logging_utils import logger

# ---------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------

def _has_meaningful_text(s: str) -> bool:
    return bool(s and s.strip() and len(s.strip()) > 10)

@lru_cache(maxsize=1)
def _get_reader(langs: tuple = ("es", "en"), gpu: bool = False) -> easyocr.Reader:
    """
    Crea y cachea un lector de EasyOCR.
    - langs: idiomas (prioriza 'es'; 'en' ayuda con números / anglicismos)
    - gpu=False por defecto (CPU)
    """
    logger.info(f"[OCR] Inicializando EasyOCR Reader langs={langs} gpu={gpu}")
    return easyocr.Reader(list(langs), gpu=gpu, verbose=False)

def _easy_text_from_image(img: Image.Image, langs: tuple = ("es", "en")) -> str:
    """
    Ejecuta OCR sobre una imagen PIL usando EasyOCR (parágrafos).
    """
    reader = _get_reader(langs=langs, gpu=False)  # GPU=False para portabilidad
    # EasyOCR acepta ruta o np.array; convertimos a array para evitar reabrir archivo
    arr = np.array(img.convert("RGB"))
    # detail=0 => devuelve solo los textos; paragraph=True => une líneas contiguas
    parts: List[str] = reader.readtext(arr, detail=0, paragraph=True)
    text = "\n".join(p.strip() for p in parts if isinstance(p, str) and p.strip())
    return text

# ---------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------

def ocr_image(path: str) -> str:
    """OCR para imagen (png/jpg/jpeg/webp) con EasyOCR."""
    img = Image.open(path)
    try:
        txt = _easy_text_from_image(img, langs=("es", "en"))
        return txt or ""
    except Exception as e:
        logger.exception(f"[OCR] Falló EasyOCR en imagen '{path}': {e}")
        return ""

def extract_pdf_text(path: str, dpi: int = 200, max_pages_ocr: Optional[int] = None) -> str:
    """
    PDF → texto. Primero capa de texto (pdfplumber); si no hay, OCR de páginas con EasyOCR.
    max_pages_ocr: si se indica, limita cuántas páginas se ocr-ean (útil p/depurar).
    """
    # 1) Intento de texto embebido (rápido y preciso si existe)
    try:
        text_parts = []
        with pdfplumber.open(path) as pdf:
            for p in pdf.pages:
                t = p.extract_text() or ""
                if t:
                    text_parts.append(t)
        text_joined = "\n".join(text_parts).strip()
        if _has_meaningful_text(text_joined):
            return text_joined
    except Exception as e:
        logger.warning(f"[OCR] pdfplumber falló en '{path}': {e} — se intenta OCR")

    # 2) OCR por páginas (PDF escaneado)
    try:
        images = convert_from_path(path, dpi=dpi)
    except Exception as e:
        logger.exception(f"[OCR] convert_from_path falló en '{path}': {e}")
        return ""

    ocr_parts: List[str] = []
    for i, img in enumerate(images):
        if isinstance(max_pages_ocr, int) and i >= max_pages_ocr:
            break
        try:
            txt = _easy_text_from_image(img, langs=("es", "en"))
            if txt:
                ocr_parts.append(txt)
        except Exception as e:
            logger.exception(f"[OCR] EasyOCR falló en página {i} de '{path}': {e}")

    return "\n".join(ocr_parts).strip()

def extract_text_from_file(path: str, mimetype: str | None) -> Tuple[str, str]:
    """
    Detecta por mimetype o extensión y extrae texto.
    Retorna (texto, tipo_detectado) donde tipo_detectado ∈ {"pdf","image"}.
    """
    mt = (mimetype or "").lower()
    ext = os.path.splitext(path)[1].lower()

    # PDF
    if "pdf" in mt or ext == ".pdf":
        return extract_pdf_text(path), "pdf"

    # Imagen
    if any(x in mt for x in ("image/",)) or ext in (".png", ".jpg", ".jpeg", ".webp"):
        return ocr_image(path), "image"

    # Por defecto intenta como imagen
    try:
        return ocr_image(path), "image"
    except Exception:
        return "", "unknown"