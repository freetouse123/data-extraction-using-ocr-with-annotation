import os
import io
import math
import base64
from typing import Optional

from pdf2image import convert_from_path
from reportlab.pdfgen import canvas
from reportlab.lib import pagesizes
from PIL import Image, ImageSequence
from pypdf import PdfWriter, PdfReader

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from dotenv import load_dotenv

from utils.helper import _load_images, _dist
from config.config import Config
load_dotenv()


class SearchablePDFConverter:
    """
    Convert PDF or Image files (single or folder) into searchable PDFs
    using Azure Document Intelligence (prebuilt-layout).
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        key: Optional[str] = None
    ):
        self.client = DocumentIntelligenceClient(
            endpoint=endpoint or os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT"),
            credential=AzureKeyCredential(
                key or os.getenv("DOCUMENT_INTELLIGENCE_KEY")
            ),
        )

    3
    def _analyze_document(self, file_path: str):
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        analyze_request = {
            "base64Source": base64.b64encode(file_bytes).decode("utf-8")
        }

        poller = self.client.begin_analyze_document(
            "prebuilt-layout",
            analyze_request,
            headers={"x-ms-useragent": "searchable-pdf-blog/1.0.0"}
        )
        

        return poller.result()

    def _create_searchable_pdf(
        self,
        image_pages,
        ocr_result,
        output_file
    ):
        output_pdf = PdfWriter()

        for page_idx, page in enumerate(ocr_result.pages):
            img = image_pages[page_idx]
            overlay_stream = io.BytesIO()

            if img.height > img.width:
                page_scale = img.height / pagesizes.letter[1]
            else:
                page_scale = img.width / pagesizes.letter[1]

            page_width = img.width / page_scale
            page_height = img.height / page_scale

            scale = (page_width / page.width + page_height / page.height) / 2

            pdf_canvas = canvas.Canvas(
                overlay_stream,
                pagesize=(page_width, page_height)
            )

            pdf_canvas.drawInlineImage(
                img,
                0,
                0,
                width=page_width,
                height=page_height,
                preserveAspectRatio=True,
            )

            text = pdf_canvas.beginText()
            text.setTextRenderMode(3)  # Invisible text

            for word in page.words:
                polygon = word.polygon

                desired_width = max(
                    _dist(polygon, 0, 2),
                    _dist(polygon, 6, 4)
                ) * scale

                desired_height = max(
                    _dist(polygon, 2, 4),
                    _dist(polygon, 0, 6)
                ) * scale

                font_size = desired_height
                actual_width = pdf_canvas.stringWidth(
                    word.content,
                    Config().DEFAULT_FONT,
                    font_size,
                )

                x0, y0 = polygon[0], polygon[1]
                x1, y1 = polygon[2], polygon[3]
                angle = math.atan2(y1 - y0, x1 - x0)

                x = polygon[6] * scale
                y = page_height - polygon[7] * scale

                text.setFont(Config().DEFAULT_FONT, font_size)
                text.setTextTransform(
                    math.cos(angle),
                    -math.sin(angle),
                    math.sin(angle),
                    math.cos(angle),
                    x,
                    y,
                )

                text.setHorizScale(
                    (desired_width / max(actual_width, 1)) * 100
                )

                text.textOut(word.content + " ")

            pdf_canvas.drawText(text)
            pdf_canvas.showPage()
            pdf_canvas.save()

            overlay_stream.seek(0)
            overlay_pdf = PdfReader(overlay_stream)
            output_pdf.add_page(overlay_pdf.pages[0])

        with open(output_file, "wb") as f:
            output_pdf.write(f)

    
    def process_file(self, input_file: str, output_file: str):
        print(f"📄 Processing file: {input_file}")
        images = _load_images(input_file)
        ocr_result = self._analyze_document(input_file)
        self._create_searchable_pdf(images, ocr_result, output_file)
        print(f"✔ Saved: {output_file}")

    def process_path(
        self,
        input_path: str,
        output_path: Optional[str] = None
    ):
        if os.path.isfile(input_path):
            output_file = (
                output_path
                or input_path + ".ocr.pdf"
            )
            self.process_file(input_path, output_file)
            return

        if not os.path.isdir(input_path):
            raise ValueError(f"Invalid path: {input_path}")

        os.makedirs(output_path, exist_ok=True)

        for filename in os.listdir(input_path):
            if not filename.lower().endswith(Config().SUPPORTED_EXTENSIONS):
                continue

            input_file = os.path.join(input_path, filename)
            output_file = os.path.join(
                output_path,
                filename + ".ocr.pdf"
            )

            try:
                self.process_file(input_file, output_file)
            except Exception as e:
                print(f"❌ Failed: {filename} → {e}")
