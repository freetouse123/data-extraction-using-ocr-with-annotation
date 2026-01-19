# # import streamlit as st
# # import fitz  # PyMuPDF
# # import base64
# # import os
# # import io
# # from PIL import Image
# # from azure.ai.vision.imageanalysis import ImageAnalysisClient
# # from azure.ai.vision.imageanalysis.models import VisualFeatures
# # from azure.core.credentials import AzureKeyCredential
# # from streamlit.components.v1 import html
# # from dotenv import load_dotenv
# # load_dotenv()
# # # ==========================
# # # CONFIG
# # # ==========================
# # VISION_ENDPOINT = os.getenv("VISION_ENDPOINT")
# # VISION_KEY = os.getenv("VISION_KEY")

# # if not VISION_ENDPOINT or not VISION_KEY:
# #     st.error("❌ Please set VISION_ENDPOINT and VISION_KEY environment variables")
# #     st.stop()

# # from src.image_data_extraction import Pdf2ImageDataExtractor
# # from utils.helper import normalize_ocr
# # extractor = Pdf2ImageDataExtractor()



# # # ==========================
# # # RENDER IMAGE + HOVER ANNOTATIONS
# # # ==========================
# # def render_annotated_image(image_bytes, annotations):
# #     img_b64 = base64.b64encode(image_bytes).decode()

# #     boxes_html = ""
# #     for ann in annotations:
# #         boxes_html += f"""
# #         <div class="bbox"
# #              style="
# #              left:{ann['left']*100}%;
# #              top:{ann['top']*100}%;
# #              width:{ann['width']*100}%;
# #              height:{ann['height']*100}%;
# #              "
# #              title="{ann['text']}">
# #         </div>
# #         """

# #     html_code = f"""
# #     <style>
# #     .container {{
# #         position: relative;
# #         width: 100%;
# #     }}
# #     .container img {{
# #         width: 100%;
# #     }}
# #     .bbox {{
# #         position: absolute;
# #         border: 2px solid rgba(255, 0, 0, 0.4);
# #         background: rgba(255, 0, 0, 0.05);
# #         cursor: pointer;
# #     }}
# #     .bbox:hover {{
# #         background: rgba(255, 0, 0, 0.15);
# #     }}
# #     </style>

# #     <div class="container">
# #         <img src="data:image/png;base64,{img_b64}">
# #         {boxes_html}
# #     </div>
# #     """

# #     html(html_code, height=900, scrolling=True)

# # import asyncio
# # st.set_page_config(layout="wide")
# # st.title("📄 PDF OCR Annotation Viewer (Hover to See Text)")

# # uploaded_pdf = st.file_uploader("Upload a scanned PDF", type=["pdf"])


# # async def process_pdf(pdf_bytes):
# #     images = await extractor.pdf_to_images(pdf_bytes)

# #     st.success(f"Converted {len(images)} pages")

# #     for idx, image_bytes in enumerate(images):
# #         st.subheader(f"Page {idx + 1}")

# #         with st.spinner("Running OCR..."):
# #             ocr_result = await extractor.extract_text_from_image(image_bytes)

# #         img = Image.open(io.BytesIO(image_bytes))
# #         width, height = img.size

# #         annotations = await normalize_ocr(ocr_result, width, height)

# #         if not annotations:
# #             st.warning("No text detected on this page")
# #         else:
# #             render_annotated_image(image_bytes, annotations)


# # if uploaded_pdf:
# #     pdf_bytes = uploaded_pdf.read()

# #     with st.spinner("Converting PDF to images..."):
# #         asyncio.run(process_pdf(pdf_bytes))

# """
# Streamlit PDF Annotation Viewer with Custom HTML Viewer
# Interactive hover tooltips for annotations
# """

# import streamlit as st
# import streamlit.components.v1 as components
# import fitz  # PyMuPDF
# import os
# import base64
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from azure.ai.vision.imageanalysis import ImageAnalysisClient
# from azure.ai.vision.imageanalysis.models import VisualFeatures
# from azure.core.credentials import AzureKeyCredential
# from dotenv import load_dotenv
# import time
# from typing import List, Dict, Tuple
# import json

# load_dotenv()

# # ==========================
# # CONFIG
# # ==========================
# VISION_ENDPOINT = os.getenv("VISION_ENDPOINT")
# VISION_KEY = os.getenv("VISION_KEY")
# BATCH_SIZE = 5

# if not VISION_ENDPOINT or not VISION_KEY:
#     st.error("❌ Please set VISION_ENDPOINT and VISION_KEY environment variables")
#     st.stop()



# # ==========================
# # BATCH PROCESSOR
# # ==========================
# class BatchProcessor:
#     def __init__(self, processor: PDFProcessor, batch_size: int = 5):
#         self.processor = processor
#         self.batch_size = batch_size
    
#     def process_batch(self, images_data: List[Tuple], batch_id: int) -> Dict:
#         """Process a batch of images"""
#         batch_results = []
        
#         for page_num, img_bytes, width, height in images_data:
#             ocr_result = self.processor.extract_text_from_image(img_bytes)
#             annotations = self.processor.normalize_ocr(ocr_result, width, height)
            
#             batch_results.append({
#                 'page_num': page_num,
#                 'annotations': annotations,
#                 'width': width,
#                 'height': height
#             })
        
#         return {
#             'batch_id': batch_id,
#             'results': batch_results
#         }
    
#     def process_all_batches(self, images_data: List[Tuple]) -> List[Dict]:
#         """Process all images in parallel batches"""
#         batches = [
#             images_data[i:i + self.batch_size] 
#             for i in range(0, len(images_data), self.batch_size)
#         ]
        
#         all_results = []
        
#         with ThreadPoolExecutor(max_workers=3) as executor:
#             futures = {
#                 executor.submit(self.process_batch, batch, idx): idx 
#                 for idx, batch in enumerate(batches)
#             }
            
#             for future in as_completed(futures):
#                 batch_result = future.result()
#                 all_results.append(batch_result)
        
#         all_results.sort(key=lambda x: x['batch_id'])
        
#         flattened = []
#         for batch in all_results:
#             flattened.extend(batch['results'])
        
#         return flattened


# # ==========================
# # HTML PDF VIEWER GENERATOR
# # ==========================
# def generate_pdf_viewer_html(display_images: List[Tuple], ocr_results: List[Dict]) -> str:
#     """Generate HTML viewer with annotations"""
    
#     # Scale factor between OCR resolution and display resolution
#     ocr_dpi = 300
#     display_dpi = 150
#     scale_factor = display_dpi / ocr_dpi
    
#     # Build pages HTML
#     pages_html = ""
#     for page_num, img_base64, display_width, display_height in display_images:
#         # Get annotations for this page
#         page_annotations = []
#         for result in ocr_results:
#             if result['page_num'] == page_num:
#                 page_annotations = result['annotations']
#                 break
        
#         # Build annotation boxes HTML
#         annotations_html = ""
#         for idx, ann in enumerate(page_annotations):
#             # Scale coordinates from OCR resolution to display resolution
#             x = ann['x0'] * scale_factor
#             y = ann['y0'] * scale_factor
#             width = (ann['x1'] - ann['x0']) * scale_factor
#             height = (ann['y1'] - ann['y0']) * scale_factor
            
#             # Escape text for HTML
#             text = ann['text'].replace('"', '&quot;').replace("'", "&#39;").replace("<", "&lt;").replace(">", "&gt;")
            
#             annotations_html += f'''
#             <div class="annotation-box" 
#                  style="left: {x}px; top: {y}px; width: {width}px; height: {height}px;"
#                  data-text="{text}">
#                 <div class="tooltip">{text}</div>
#             </div>
#             '''
        
#         pages_html += f'''
#         <div class="pdf-page" id="page-{page_num + 1}">
#             <div class="page-header">Page {page_num + 1}</div>
#             <div class="page-container" style="width: {display_width}px; height: {display_height}px;">
#                 <img src="data:image/png;base64,{img_base64}" 
#                      alt="Page {page_num + 1}" 
#                      style="width: {display_width}px; height: {display_height}px;">
#                 <div class="annotations-layer">
#                     {annotations_html}
#                 </div>
#             </div>
#         </div>
#         '''
    
#     # Complete HTML with CSS and JavaScript
#     html = f'''
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <style>
#             * {{
#                 margin: 0;
#                 padding: 0;
#                 box-sizing: border-box;
#             }}
            
#             body {{
#                 font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
#                 background: #1a1a2e;
#                 padding: 20px;
#             }}
            
#             .viewer-container {{
#                 max-width: 100%;
#                 margin: 0 auto;
#             }}
            
#             .controls {{
#                 position: sticky;
#                 top: 0;
#                 background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#                 padding: 15px 20px;
#                 border-radius: 12px;
#                 margin-bottom: 20px;
#                 display: flex;
#                 justify-content: space-between;
#                 align-items: center;
#                 z-index: 1000;
#                 box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
#             }}
            
#             .controls-left {{
#                 display: flex;
#                 align-items: center;
#                 gap: 15px;
#             }}
            
#             .controls h2 {{
#                 color: white;
#                 font-size: 1.2rem;
#                 font-weight: 600;
#             }}
            
#             .page-nav {{
#                 display: flex;
#                 align-items: center;
#                 gap: 10px;
#             }}
            
#             .page-nav button {{
#                 background: rgba(255, 255, 255, 0.2);
#                 border: none;
#                 color: white;
#                 padding: 8px 15px;
#                 border-radius: 8px;
#                 cursor: pointer;
#                 font-size: 14px;
#                 transition: all 0.2s;
#             }}
            
#             .page-nav button:hover {{
#                 background: rgba(255, 255, 255, 0.3);
#                 transform: translateY(-1px);
#             }}
            
#             .page-nav select {{
#                 background: rgba(255, 255, 255, 0.2);
#                 border: none;
#                 color: white;
#                 padding: 8px 12px;
#                 border-radius: 8px;
#                 cursor: pointer;
#                 font-size: 14px;
#             }}
            
#             .page-nav select option {{
#                 background: #333;
#                 color: white;
#             }}
            
#             .toggle-btn {{
#                 background: rgba(255, 255, 255, 0.2);
#                 border: none;
#                 color: white;
#                 padding: 8px 15px;
#                 border-radius: 8px;
#                 cursor: pointer;
#                 font-size: 14px;
#                 transition: all 0.2s;
#             }}
            
#             .toggle-btn:hover {{
#                 background: rgba(255, 255, 255, 0.3);
#             }}
            
#             .toggle-btn.active {{
#                 background: rgba(255, 255, 255, 0.4);
#                 box-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
#             }}
            
#             .pdf-page {{
#                 margin-bottom: 30px;
#                 background: #16213e;
#                 border-radius: 12px;
#                 padding: 20px;
#                 box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
#             }}
            
#             .page-header {{
#                 color: #a0a0a0;
#                 font-size: 14px;
#                 margin-bottom: 15px;
#                 padding-bottom: 10px;
#                 border-bottom: 1px solid #2a2a4a;
#             }}
            
#             .page-container {{
#                 position: relative;
#                 margin: 0 auto;
#                 box-shadow: 0 4px 25px rgba(0, 0, 0, 0.4);
#                 border-radius: 4px;
#                 overflow: hidden;
#             }}
            
#             .page-container img {{
#                 display: block;
#             }}
            
#             .annotations-layer {{
#                 position: absolute;
#                 top: 0;
#                 left: 0;
#                 width: 100%;
#                 height: 100%;
#                 pointer-events: none;
#             }}
            
#             .annotations-layer.active {{
#                 pointer-events: auto;
#             }}
            
#             .annotation-box {{
#                 position: absolute;
#                 border: 2px solid rgba(102, 126, 234, 0.8);
#                 background: rgba(102, 126, 234, 0.1);
#                 cursor: pointer;
#                 pointer-events: auto;
#                 transition: all 0.2s ease;
#                 border-radius: 3px;
#             }}
            
#             .annotation-box:hover {{
#                 background: rgba(102, 126, 234, 0.25);
#                 border-color: rgba(102, 126, 234, 1);
#                 box-shadow: 0 0 15px rgba(102, 126, 234, 0.5);
#                 z-index: 100;
#             }}
            
#             .tooltip {{
#                 position: absolute;
#                 bottom: calc(100% + 10px);
#                 left: 50%;
#                 transform: translateX(-50%);
#                 background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
#                 color: #fff;
#                 padding: 12px 16px;
#                 border-radius: 10px;
#                 font-size: 14px;
#                 line-height: 1.5;
#                 white-space: normal;
#                 max-width: 350px;
#                 min-width: 150px;
#                 opacity: 0;
#                 visibility: hidden;
#                 transition: all 0.25s ease;
#                 z-index: 1000;
#                 box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
#                 border: 1px solid rgba(102, 126, 234, 0.3);
#                 word-wrap: break-word;
#             }}
            
#             .tooltip::before {{
#                 content: '';
#                 position: absolute;
#                 top: 100%;
#                 left: 50%;
#                 transform: translateX(-50%);
#                 border: 8px solid transparent;
#                 border-top-color: #16213e;
#             }}
            
#             .annotation-box:hover .tooltip {{
#                 opacity: 1;
#                 visibility: visible;
#                 bottom: calc(100% + 15px);
#             }}
            
#             /* Tooltip position adjustment for boxes near edges */
#             .annotation-box.tooltip-right .tooltip {{
#                 left: 0;
#                 transform: translateX(0);
#             }}
            
#             .annotation-box.tooltip-right .tooltip::before {{
#                 left: 20px;
#             }}
            
#             .annotation-box.tooltip-left .tooltip {{
#                 left: auto;
#                 right: 0;
#                 transform: translateX(0);
#             }}
            
#             .annotation-box.tooltip-left .tooltip::before {{
#                 left: auto;
#                 right: 20px;
#             }}
            
#             .annotation-box.tooltip-bottom .tooltip {{
#                 bottom: auto;
#                 top: calc(100% + 10px);
#             }}
            
#             .annotation-box.tooltip-bottom .tooltip::before {{
#                 top: auto;
#                 bottom: 100%;
#                 border: 8px solid transparent;
#                 border-bottom-color: #16213e;
#             }}
            
#             .annotation-box.tooltip-bottom:hover .tooltip {{
#                 bottom: auto;
#                 top: calc(100% + 15px);
#             }}
            
#             /* Hide annotations when disabled */
#             .annotations-hidden .annotation-box {{
#                 opacity: 0;
#                 pointer-events: none;
#             }}
            
#             /* Zoom controls */
#             .zoom-controls {{
#                 display: flex;
#                 align-items: center;
#                 gap: 8px;
#             }}
            
#             .zoom-controls button {{
#                 background: rgba(255, 255, 255, 0.2);
#                 border: none;
#                 color: white;
#                 width: 32px;
#                 height: 32px;
#                 border-radius: 6px;
#                 cursor: pointer;
#                 font-size: 18px;
#                 display: flex;
#                 align-items: center;
#                 justify-content: center;
#                 transition: all 0.2s;
#             }}
            
#             .zoom-controls button:hover {{
#                 background: rgba(255, 255, 255, 0.3);
#             }}
            
#             .zoom-level {{
#                 color: white;
#                 font-size: 14px;
#                 min-width: 50px;
#                 text-align: center;
#             }}
            
#             /* Stats bar */
#             .stats-bar {{
#                 background: rgba(255, 255, 255, 0.1);
#                 padding: 8px 15px;
#                 border-radius: 8px;
#                 color: white;
#                 font-size: 13px;
#                 display: flex;
#                 gap: 20px;
#             }}
            
#             .stat-item {{
#                 display: flex;
#                 align-items: center;
#                 gap: 5px;
#             }}
            
#             .stat-item span {{
#                 opacity: 0.7;
#             }}
            
#             .stat-value {{
#                 font-weight: 600;
#             }}
            
#             /* Scrollbar styling */
#             ::-webkit-scrollbar {{
#                 width: 10px;
#             }}
            
#             ::-webkit-scrollbar-track {{
#                 background: #1a1a2e;
#             }}
            
#             ::-webkit-scrollbar-thumb {{
#                 background: #667eea;
#                 border-radius: 5px;
#             }}
            
#             ::-webkit-scrollbar-thumb:hover {{
#                 background: #764ba2;
#             }}
#         </style>
#     </head>
#     <body>
#         <div class="viewer-container" id="viewer">
#             <div class="controls">
#                 <div class="controls-left">
#                     <h2>📄 PDF Viewer</h2>
#                     <div class="page-nav">
#                         <button onclick="prevPage()">◀ Prev</button>
#                         <select id="pageSelect" onchange="goToPage(this.value)">
#                             {generate_page_options(len(display_images))}
#                         </select>
#                         <button onclick="nextPage()">Next ▶</button>
#                     </div>
#                     <div class="zoom-controls">
#                         <button onclick="zoomOut()">−</button>
#                         <span class="zoom-level" id="zoomLevel">100%</span>
#                         <button onclick="zoomIn()">+</button>
#                     </div>
#                 </div>
#                 <div class="controls-right" style="display: flex; gap: 10px; align-items: center;">
#                     <div class="stats-bar">
#                         <div class="stat-item">
#                             <span>📄</span>
#                             <span class="stat-value">{len(display_images)}</span>
#                             <span>pages</span>
#                         </div>
#                         <div class="stat-item">
#                             <span>📝</span>
#                             <span class="stat-value">{sum(len(r['annotations']) for r in ocr_results)}</span>
#                             <span>annotations</span>
#                         </div>
#                     </div>
#                     <button class="toggle-btn active" id="toggleAnnotations" onclick="toggleAnnotations()">
#                         👁 Annotations
#                     </button>
#                 </div>
#             </div>
            
#             <div class="pages-wrapper" id="pagesWrapper">
#                 {pages_html}
#             </div>
#         </div>
        
#         <script>
#             let currentPage = 1;
#             const totalPages = {len(display_images)};
#             let zoomLevel = 100;
#             let annotationsVisible = true;
            
#             // Initialize tooltip positions
#             document.addEventListener('DOMContentLoaded', function() {{
#                 const annotations = document.querySelectorAll('.annotation-box');
#                 annotations.forEach(function(ann) {{
#                     const rect = ann.getBoundingClientRect();
#                     const container = ann.closest('.page-container');
#                     const containerRect = container.getBoundingClientRect();
                    
#                     // Check if tooltip would overflow
#                     if (rect.left < 100) {{
#                         ann.classList.add('tooltip-right');
#                     }} else if (containerRect.right - rect.right < 100) {{
#                         ann.classList.add('tooltip-left');
#                     }}
                    
#                     if (rect.top < 100) {{
#                         ann.classList.add('tooltip-bottom');
#                     }}
#                 }});
#             }});
            
#             function goToPage(pageNum) {{
#                 currentPage = parseInt(pageNum);
#                 const element = document.getElementById('page-' + currentPage);
#                 if (element) {{
#                     element.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
#                 }}
#                 document.getElementById('pageSelect').value = currentPage;
#             }}
            
#             function prevPage() {{
#                 if (currentPage > 1) {{
#                     goToPage(currentPage - 1);
#                 }}
#             }}
            
#             function nextPage() {{
#                 if (currentPage < totalPages) {{
#                     goToPage(currentPage + 1);
#                 }}
#             }}
            
#             function zoomIn() {{
#                 if (zoomLevel < 200) {{
#                     zoomLevel += 25;
#                     applyZoom();
#                 }}
#             }}
            
#             function zoomOut() {{
#                 if (zoomLevel > 50) {{
#                     zoomLevel -= 25;
#                     applyZoom();
#                 }}
#             }}
            
#             function applyZoom() {{
#                 const wrapper = document.getElementById('pagesWrapper');
#                 wrapper.style.transform = 'scale(' + (zoomLevel / 100) + ')';
#                 wrapper.style.transformOrigin = 'top center';
#                 document.getElementById('zoomLevel').textContent = zoomLevel + '%';
#             }}
            
#             function toggleAnnotations() {{
#                 annotationsVisible = !annotationsVisible;
#                 const wrapper = document.getElementById('pagesWrapper');
#                 const btn = document.getElementById('toggleAnnotations');
                
#                 if (annotationsVisible) {{
#                     wrapper.classList.remove('annotations-hidden');
#                     btn.classList.add('active');
#                     btn.textContent = '👁 Annotations';
#                 }} else {{
#                     wrapper.classList.add('annotations-hidden');
#                     btn.classList.remove('active');
#                     btn.textContent = '👁‍🗨 Show Annotations';
#                 }}
#             }}
            
#             // Keyboard navigation
#             document.addEventListener('keydown', function(e) {{
#                 if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{
#                     prevPage();
#                 }} else if (e.key === 'ArrowRight' || e.key === 'PageDown') {{
#                     nextPage();
#                 }} else if (e.key === '+' || e.key === '=') {{
#                     zoomIn();
#                 }} else if (e.key === '-') {{
#                     zoomOut();
#                 }}
#             }});
            
#             // Track current page on scroll
#             window.addEventListener('scroll', function() {{
#                 const pages = document.querySelectorAll('.pdf-page');
#                 pages.forEach(function(page, index) {{
#                     const rect = page.getBoundingClientRect();
#                     if (rect.top <= 150 && rect.bottom > 150) {{
#                         currentPage = index + 1;
#                         document.getElementById('pageSelect').value = currentPage;
#                     }}
#                 }});
#             }});
#         </script>
#     </body>
#     </html>
#     '''
    
#     return html


# def generate_page_options(total_pages: int) -> str:
#     """Generate HTML options for page selector"""
#     options = ""
#     for i in range(1, total_pages + 1):
#         options += f'<option value="{i}">Page {i} of {total_pages}</option>'
#     return options


# # ==========================
# # STREAMLIT UI
# # ==========================
# def main():
#     st.set_page_config(
#         layout="wide", 
#         page_title="PDF OCR Viewer",
#         initial_sidebar_state="collapsed"
#     )
    
#     # Custom CSS
#     st.markdown("""
#         <style>
#         .main {
#             padding: 1rem;
#         }
#         .stButton button {
#             width: 100%;
#             background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#             color: white;
#             font-weight: 600;
#             padding: 0.75rem 2rem;
#             border-radius: 10px;
#             border: none;
#             font-size: 1.1rem;
#             transition: all 0.3s ease;
#         }
#         .stButton button:hover {
#             transform: translateY(-2px);
#             box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
#         }
#         h1 {
#             color: #1a1a2e;
#             font-weight: 700;
#             margin-bottom: 0.5rem;
#         }
#         .subtitle {
#             color: #6c757d;
#             font-size: 1.1rem;
#             margin-bottom: 2rem;
#         }
#         iframe {
#             border: none;
#             border-radius: 12px;
#         }
#         </style>
#     """, unsafe_allow_html=True)
    
#     st.title("📄 PDF OCR Annotation Viewer")
#     st.markdown('<p class="subtitle">Upload a PDF to extract and visualize text with interactive hover annotations</p>', 
#                 unsafe_allow_html=True)
    
#     # Initialize session state
#     if 'viewer_html' not in st.session_state:
#         st.session_state.viewer_html = None
#         st.session_state.processing_stats = None
#         st.session_state.all_annotations = []
    
#     # File upload
#     uploaded_file = st.file_uploader(
#         "Choose a PDF file",
#         type=['pdf'],
#         help="Upload a scanned or digital PDF document",
#         label_visibility="collapsed"
#     )
    
#     if uploaded_file:
#         pdf_bytes = uploaded_file.read()
        
#         # Show process button if not processed
#         if st.session_state.viewer_html is None:
#             st.markdown("---")
#             col1, col2, col3 = st.columns([1, 2, 1])
            
#             with col2:
#                 if st.button("🚀 Extract Text & Create Interactive Viewer", type="primary"):
                    
#                     processor = PDFProcessor()
#                     batch_processor = BatchProcessor(processor, batch_size=BATCH_SIZE)
                    
#                     # Progress tracking
#                     progress_placeholder = st.empty()
                    
#                     with progress_placeholder.container():
#                         progress_bar = st.progress(0)
#                         status_text = st.empty()
                        
#                         start_time = time.time()
                        
#                         # Step 1: Convert to images for OCR
#                         status_text.markdown("**📄 Converting PDF to images for OCR...**")
#                         images_for_ocr = processor.pdf_to_images_for_ocr(pdf_bytes)
#                         progress_bar.progress(0.2)
                        
#                         # Step 2: OCR Processing
#                         status_text.markdown(f"**🔍 Processing {len(images_for_ocr)} pages with Azure OCR...**")
#                         all_results = batch_processor.process_all_batches(images_for_ocr)
#                         progress_bar.progress(0.6)
                        
#                         # Step 3: Convert to display images
#                         status_text.markdown("**🖼️ Preparing display images...**")
#                         display_images = processor.pdf_to_images_for_display(pdf_bytes)
#                         progress_bar.progress(0.8)
                        
#                         # Step 4: Generate HTML viewer
#                         status_text.markdown("**✨ Building interactive viewer...**")
#                         viewer_html = generate_pdf_viewer_html(display_images, all_results)
#                         progress_bar.progress(1.0)
                        
#                         end_time = time.time()
#                         processing_time = end_time - start_time
                        
#                         status_text.markdown("**✅ Processing complete!**")
#                         time.sleep(0.5)
                    
#                     # Clear progress
#                     progress_placeholder.empty()
                    
#                     # Store results
#                     st.session_state.viewer_html = viewer_html
#                     st.session_state.all_annotations = all_results
#                     st.session_state.processing_stats = {
#                         'pages': len(all_results),
#                         'annotations': sum(len(r['annotations']) for r in all_results),
#                         'time': processing_time
#                     }
                    
#                     st.success("✅ Interactive viewer created!")
#                     time.sleep(0.5)
#                     st.rerun()
        
#         # Display viewer
#         if st.session_state.viewer_html:
#             # Stats
#             if st.session_state.processing_stats:
#                 stats = st.session_state.processing_stats
                
#                 col1, col2, col3, col4, col5 = st.columns(5)
                
#                 with col1:
#                     st.metric("📄 Pages", stats['pages'])
#                 with col2:
#                     st.metric("📝 Text Regions", stats['annotations'])
#                 with col3:
#                     st.metric("⚡ Time", f"{stats['time']:.1f}s")
#                 with col4:
#                     st.metric("📊 Speed", f"{stats['time']/stats['pages']:.2f}s/pg")
#                 with col5:
#                     if st.button("🔄 New PDF"):
#                         st.session_state.viewer_html = None
#                         st.session_state.processing_stats = None
#                         st.session_state.all_annotations = []
#                         st.rerun()
            
#             st.markdown("---")
#             st.info("💡 **Hover over blue boxes** to see detected text. Use controls to navigate, zoom, or toggle annotations.")
            
#             # Render HTML viewer
#             components.html(
#                 st.session_state.viewer_html,
#                 height=900,
#                 scrolling=True
#             )
            
#             # Download extracted text
#             st.markdown("---")
#             col_a, col_b, col_c = st.columns([1, 1, 1])
            
#             with col_b:
#                 all_text = ""
#                 for result in st.session_state.all_annotations:
#                     all_text += f"\n{'='*50}\nPage {result['page_num'] + 1}\n{'='*50}\n\n"
#                     for ann in result['annotations']:
#                         all_text += f"{ann['text']}\n"
                
#                 st.download_button(
#                     label="📥 Download Extracted Text",
#                     data=all_text,
#                     file_name="extracted_text.txt",
#                     mime="text/plain",
#                     use_container_width=True
#                 )


# if __name__ == "__main__":
#     main()







