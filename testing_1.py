import streamlit as st
import fitz  # PyMuPDF
import base64
import os
import io
from PIL import Image
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from streamlit.components.v1 import html
from dotenv import load_dotenv
load_dotenv()
# ==========================
# CONFIG
# ==========================
VISION_ENDPOINT = os.getenv("VISION_ENDPOINT")
VISION_KEY = os.getenv("VISION_KEY")

if not VISION_ENDPOINT or not VISION_KEY:
    st.error("❌ Please set VISION_ENDPOINT and VISION_KEY environment variables")
    st.stop()

from src.image_data_extraction import Pdf2ImageDataExtractor
from utils.helper import normalize_ocr
extractor = Pdf2ImageDataExtractor()



# ==========================
# RENDER IMAGE + HOVER ANNOTATIONS
# ==========================
def render_annotated_image(image_bytes, annotations):
    img_b64 = base64.b64encode(image_bytes).decode()

    boxes_html = ""
    for ann in annotations:
        boxes_html += f"""
        <div class="bbox"
             style="
             left:{ann['left']*100}%;
             top:{ann['top']*100}%;
             width:{ann['width']*100}%;
             height:{ann['height']*100}%;
             "
             title="{ann['text']}">
        </div>
        """

    html_code = f"""
    <style>
    .container {{
        position: relative;
        width: 100%;
    }}
    .container img {{
        width: 100%;
    }}
    .bbox {{
        position: absolute;
        border: 2px solid rgba(255, 0, 0, 0.4);
        background: rgba(255, 0, 0, 0.05);
        cursor: pointer;
    }}
    .bbox:hover {{
        background: rgba(255, 0, 0, 0.15);
    }}
    </style>

    <div class="container">
        <img src="data:image/png;base64,{img_b64}">
        {boxes_html}
    </div>
    """

    html(html_code, height=900, scrolling=True)

import asyncio
st.set_page_config(layout="wide")
st.title("📄 PDF OCR Annotation Viewer (Hover to See Text)")

uploaded_pdf = st.file_uploader("Upload a scanned PDF", type=["pdf"])


async def process_pdf(pdf_bytes):
    images = await extractor.pdf_to_images(pdf_bytes)

    st.success(f"Converted {len(images)} pages")

    for idx, image_bytes in enumerate(images):
        st.subheader(f"Page {idx + 1}")

        with st.spinner("Running OCR..."):
            ocr_result = await extractor.extract_text_from_image(image_bytes)

        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size

        annotations = await normalize_ocr(ocr_result, width, height)

        if not annotations:
            st.warning("No text detected on this page")
        else:
            render_annotated_image(image_bytes, annotations)


if uploaded_pdf:
    pdf_bytes = uploaded_pdf.read()

    with st.spinner("Converting PDF to images..."):
        asyncio.run(process_pdf(pdf_bytes))