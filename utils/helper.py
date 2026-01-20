"""
Helper functions for PDF processing, OCR normalization, and HTML generation
"""
from .logger import get_logger
from typing import List, Dict, Tuple
import base64
import math
from pdf2image import convert_from_path
from PIL import Image, ImageSequence

logger = get_logger(__name__)

"""
Helper utilities for OCR processing
"""

from typing import List, Dict, Any


def normalize_ocr(ocr_result, img_width: int, img_height: int) -> List[Dict[str, Any]]:
    """
    Normalize OCR results to extract text with bounding boxes
    Returns coordinates in both normalized (0-1) and pixel formats
    """
    annotations = []
    
    if not ocr_result.read or not ocr_result.read.blocks:
        return annotations
    
    for block in ocr_result.read.blocks:
        for line in block.lines:
            # Get bounding polygon (4 points: top-left, top-right, bottom-right, bottom-left)
            polygon = line.bounding_polygon
            
            if len(polygon) >= 4:
                # Extract coordinates
                x_coords = [p.x for p in polygon]
                y_coords = [p.y for p in polygon]
                
                x_min = min(x_coords)
                x_max = max(x_coords)
                y_min = min(y_coords)
                y_max = max(y_coords)
                
                # Pixel coordinates
                bbox_pixels = {
                    'x': x_min,
                    'y': y_min,
                    'width': x_max - x_min,
                    'height': y_max - y_min
                }
                
                # Normalized coordinates (0-1)
                bbox_normalized = {
                    'x': x_min / img_width,
                    'y': y_min / img_height,
                    'width': (x_max - x_min) / img_width,
                    'height': (y_max - y_min) / img_height
                }
                
                annotation = {
                    'text': line.text,
                    'confidence': getattr(line, 'confidence', 1.0),
                    'bbox_pixels': bbox_pixels,
                    'bbox_normalized': bbox_normalized,
                    'polygon': [{'x': p.x, 'y': p.y} for p in polygon]
                }
                
                # Process individual words if available
                words = []
                for word in line.words:
                    word_polygon = word.bounding_polygon
                    if len(word_polygon) >= 4:
                        wx_coords = [p.x for p in word_polygon]
                        wy_coords = [p.y for p in word_polygon]
                        
                        words.append({
                            'text': word.text,
                            'confidence': getattr(word, 'confidence', 1.0),
                            'bbox_pixels': {
                                'x': min(wx_coords),
                                'y': min(wy_coords),
                                'width': max(wx_coords) - min(wx_coords),
                                'height': max(wy_coords) - min(wy_coords)
                            },
                            'bbox_normalized': {
                                'x': min(wx_coords) / img_width,
                                'y': min(wy_coords) / img_height,
                                'width': (max(wx_coords) - min(wx_coords)) / img_width,
                                'height': (max(wy_coords) - min(wy_coords)) / img_height
                            }
                        })
                
                annotation['words'] = words
                annotations.append(annotation)
    
    return annotations



@staticmethod
def _dist(polygon, i1, i2):
    x1, y1 = polygon[i1], polygon[i1 + 1]
    x2, y2 = polygon[i2], polygon[i2 + 1]
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

@staticmethod
def _load_images(input_file: str):
    if input_file.lower().endswith(".pdf"):
        return convert_from_path(input_file)
    return list(ImageSequence.Iterator(Image.open(input_file)))




def generate_page_options(total_pages: int) -> str:
    """Generate HTML options for page selector"""
    options = ""
    for i in range(1, total_pages + 1):
        options += f'<option value="{i}">Page {i} of {total_pages}</option>'
    return options


def generate_pdf_viewer_html(display_images: List[Tuple], ocr_results: List[Dict]) -> str:
    """
    Generate HTML viewer with annotations - properly scaled to fit container
    """
    
    # Scale factor between OCR resolution and display resolution
    ocr_dpi = 300
    display_dpi = 150
    scale_factor = display_dpi / ocr_dpi
    
    # Build pages HTML with percentage-based annotations
    pages_html = ""
    for page_num, img_base64, display_width, display_height in display_images:
        # Get annotations for this page
        page_annotations = []
        for result in ocr_results:
            if result['page_num'] == page_num:
                page_annotations = result['annotations']
                break
        
        # Build annotation boxes HTML using percentage positions
        annotations_html = ""
        for idx, ann in enumerate(page_annotations):
            # Calculate percentage positions based on original OCR dimensions
            ocr_width = ann.get('img_width', display_width / scale_factor)
            ocr_height = ann.get('img_height', display_height / scale_factor)
            
            # Convert to percentages
            left_pct = (ann['x0'] / ocr_width) * 100
            top_pct = (ann['y0'] / ocr_height) * 100
            width_pct = ((ann['x1'] - ann['x0']) / ocr_width) * 100
            height_pct = ((ann['y1'] - ann['y0']) / ocr_height) * 100
            
            # Escape text for HTML
            text = ann['text'].replace('"', '&quot;').replace("'", "&#39;").replace("<", "&lt;").replace(">", "&gt;")
            
            annotations_html += f'''
            <div class="annotation-box" 
                 style="left: {left_pct}%; top: {top_pct}%; width: {width_pct}%; height: {height_pct}%;"
                 data-text="{text}">
                <div class="tooltip">{text}</div>
            </div>
            '''
        
        # Calculate aspect ratio for proper scaling
        aspect_ratio = display_height / display_width * 100
        
        pages_html += f'''
        <div class="pdf-page" id="page-{page_num + 1}">
            <div class="page-header">Page {page_num + 1}</div>
            <div class="page-wrapper" style="padding-bottom: {aspect_ratio}%;">
                <img src="data:image/png;base64,{img_base64}" alt="Page {page_num + 1}">
                <div class="annotations-layer">
                    {annotations_html}
                </div>
            </div>
        </div>
        '''
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #1a1a2e;
                padding: 15px;
            }}
            
            .viewer-container {{
                max-width: 100%;
                margin: 0 auto;
            }}
            
            .controls {{
                position: sticky;
                top: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 12px 18px;
                border-radius: 10px;
                margin-bottom: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                z-index: 1000;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
                flex-wrap: wrap;
                gap: 10px;
            }}
            
            .controls-left {{
                display: flex;
                align-items: center;
                gap: 12px;
                flex-wrap: wrap;
            }}
            
            .controls h2 {{
                color: white;
                font-size: 1rem;
                font-weight: 600;
            }}
            
            .page-nav {{
                display: flex;
                align-items: center;
                gap: 6px;
            }}
            
            .page-nav button, .ctrl-btn {{
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                padding: 8px 14px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
                transition: all 0.2s;
            }}
            
            .page-nav button:hover, .ctrl-btn:hover {{
                background: rgba(255, 255, 255, 0.3);
            }}
            
            .ctrl-btn.active {{
                background: rgba(255, 255, 255, 0.4);
            }}
            
            .page-nav select {{
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
            }}
            
            .page-nav select option {{
                background: #333;
                color: white;
            }}
            
            .zoom-controls {{
                display: flex;
                align-items: center;
                gap: 6px;
            }}
            
            .zoom-controls button {{
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                width: 32px;
                height: 32px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
            }}
            
            .zoom-level {{
                color: white;
                font-size: 13px;
                min-width: 50px;
                text-align: center;
            }}
            
            .stats-row {{
                display: flex;
                gap: 12px;
                color: white;
                font-size: 12px;
                background: rgba(255,255,255,0.1);
                padding: 6px 12px;
                border-radius: 6px;
            }}
            
            .stat {{ display: flex; align-items: center; gap: 4px; }}
            .stat-val {{ font-weight: 700; }}
            
            .pages-wrapper {{
                transition: transform 0.3s ease;
                transform-origin: top center;
            }}
            
            .pdf-page {{
                background: #16213e;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            }}
            
            .page-header {{
                color: #a0a0a0;
                font-size: 13px;
                margin-bottom: 12px;
                padding-bottom: 10px;
                border-bottom: 1px solid #2a2a4a;
            }}
            
            /* Responsive page wrapper using padding-bottom trick */
            .page-wrapper {{
                position: relative;
                width: 100%;
                overflow: hidden;
                border-radius: 4px;
                box-shadow: 0 4px 25px rgba(0, 0, 0, 0.4);
            }}
            
            .page-wrapper img {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                object-fit: contain;
                display: block;
            }}
            
            .annotations-layer {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
            }}
            
            .annotation-box {{
                position: absolute;
                border: 2px solid rgba(102, 126, 234, 0.7);
                background: rgba(102, 126, 234, 0.08);
                cursor: pointer;
                pointer-events: auto;
                transition: all 0.2s ease;
                border-radius: 2px;
            }}
            
            .annotation-box:hover {{
                background: rgba(102, 126, 234, 0.25);
                border-color: rgba(102, 126, 234, 1);
                box-shadow: 0 0 12px rgba(102, 126, 234, 0.5);
                z-index: 100;
            }}
            
            .tooltip {{
                position: absolute;
                bottom: calc(100% + 8px);
                left: 50%;
                transform: translateX(-50%);
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #fff;
                padding: 10px 14px;
                border-radius: 8px;
                font-size: 13px;
                line-height: 1.4;
                white-space: normal;
                max-width: 300px;
                min-width: 120px;
                opacity: 0;
                visibility: hidden;
                transition: all 0.2s ease;
                z-index: 1000;
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(102, 126, 234, 0.3);
                word-wrap: break-word;
            }}
            
            .tooltip::before {{
                content: '';
                position: absolute;
                top: 100%;
                left: 50%;
                transform: translateX(-50%);
                border: 6px solid transparent;
                border-top-color: #16213e;
            }}
            
            .annotation-box:hover .tooltip {{
                opacity: 1;
                visibility: visible;
            }}
            
            .annotations-hidden .annotation-box {{
                opacity: 0;
                pointer-events: none;
            }}
            
            ::-webkit-scrollbar {{ width: 8px; }}
            ::-webkit-scrollbar-track {{ background: #1a1a2e; }}
            ::-webkit-scrollbar-thumb {{ background: #667eea; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="viewer-container" id="viewer">
            <div class="controls">
                <div class="controls-left">
                    <h2>📄 PDF Viewer</h2>
                    <div class="page-nav">
                        <button onclick="prevPage()">◀</button>
                        <select id="pageSelect" onchange="goToPage(this.value)">
                            {generate_page_options(len(display_images))}
                        </select>
                        <button onclick="nextPage()">▶</button>
                    </div>
                    <div class="zoom-controls">
                        <button onclick="zoomOut()">−</button>
                        <span class="zoom-level" id="zoomLevel">100%</span>
                        <button onclick="zoomIn()">+</button>
                    </div>
                </div>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <div class="stats-row">
                        <span class="stat">📄 <span class="stat-val">{len(display_images)}</span></span>
                        <span class="stat">📝 <span class="stat-val">{sum(len(r['annotations']) for r in ocr_results)}</span></span>
                    </div>
                    <button class="ctrl-btn active" id="toggleBtn" onclick="toggleAnnotations()">👁 Annotations</button>
                </div>
            </div>
            
            <div class="pages-wrapper" id="pagesWrapper">
                {pages_html}
            </div>
        </div>
        
        <script>
            let currentPage = 1;
            const totalPages = {len(display_images)};
            let zoomLevel = 100;
            let annotationsVisible = true;
            
            function goToPage(num) {{
                currentPage = parseInt(num);
                document.getElementById('page-' + currentPage)?.scrollIntoView({{behavior:'smooth',block:'start'}});
                document.getElementById('pageSelect').value = currentPage;
            }}
            
            function prevPage() {{ if(currentPage > 1) goToPage(currentPage - 1); }}
            function nextPage() {{ if(currentPage < totalPages) goToPage(currentPage + 1); }}
            
            function zoomIn() {{
                if (zoomLevel < 200) {{
                    zoomLevel += 25;
                    applyZoom();
                }}
            }}
            
            function zoomOut() {{
                if (zoomLevel > 50) {{
                    zoomLevel -= 25;
                    applyZoom();
                }}
            }}
            
            function applyZoom() {{
                const wrapper = document.getElementById('pagesWrapper');
                wrapper.style.transform = 'scale(' + (zoomLevel / 100) + ')';
                document.getElementById('zoomLevel').textContent = zoomLevel + '%';
            }}
            
            function toggleAnnotations() {{
                annotationsVisible = !annotationsVisible;
                const wrapper = document.getElementById('pagesWrapper');
                const btn = document.getElementById('toggleBtn');
                wrapper.classList.toggle('annotations-hidden', !annotationsVisible);
                btn.classList.toggle('active', annotationsVisible);
                btn.textContent = annotationsVisible ? '👁 Annotations' : '👁‍🗨 Show';
            }}
            
            // Track scroll position
            window.addEventListener('scroll', function() {{
                document.querySelectorAll('.pdf-page').forEach((page, idx) => {{
                    const rect = page.getBoundingClientRect();
                    if (rect.top <= 120 && rect.bottom > 120) {{
                        currentPage = idx + 1;
                        document.getElementById('pageSelect').value = currentPage;
                    }}
                }});
            }});
        </script>
    </body>
    </html>
    '''
    
    return html


def format_extracted_data_html(data: dict) -> str:
    if not isinstance(data, dict):
        return "<p>No data</p>"

    def labelize(key: str) -> str:
        return key.replace("_", " ").title()

    def safe(val):
        if val is None:
            return "—"
        return str(val).replace("<", "&lt;").replace(">", "&gt;")

    def render_table(d: dict) -> str:
        rows = ""
        for k, v in d.items():
            if isinstance(v, dict):
                rows += f"""
                <tr>
                    <td class="key">{labelize(k)}</td>
                    <td>{render_subsection(v)}</td>
                </tr>
                """
            elif isinstance(v, list):
                rows += f"""
                <tr>
                    <td class="key">{labelize(k)}</td>
                    <td>{render_list(v)}</td>
                </tr>
                """
            else:
                rows += f"""
                <tr>
                    <td class="key">{labelize(k)}</td>
                    <td class="value">{safe(v)}</td>
                </tr>
                """
        return f"<table class='kv-table'>{rows}</table>"

    def render_list(lst: list) -> str:
        if not lst:
            return "—"
        if isinstance(lst[0], dict):
            items = ""
            for idx, item in enumerate(lst, 1):
                items += f"""
                <div class="sub-card">
                    <div class="sub-title">Item {idx}</div>
                    {render_table(item)}
                </div>
                """
            return items
        return "<ul>" + "".join(f"<li>{safe(v)}</li>" for v in lst) + "</ul>"

    def render_subsection(d: dict) -> str:
        blocks = ""
        for k, v in d.items():
            if isinstance(v, dict):
                blocks += f"""
                <div class="sub-card">
                    <div class="sub-title">{labelize(k)}</div>
                    {render_table(v)}
                </div>
                """
            else:
                blocks += f"""
                <div class="inline-row">
                    <span class="inline-key">{labelize(k)}:</span>
                    <span class="inline-value">{safe(v)}</span>
                </div>
                """
        return blocks

    html = ""

    for section, content in data.items():
        html += f"""
        <div class="batch-card">
            <div class="batch-header">
                📌 {labelize(section)}
            </div>
            <div class="batch-content">
        """

        if isinstance(content, dict):
            html += render_table(content)
        elif isinstance(content, list):
            html += render_list(content)
        else:
            html += f"<p>{safe(content)}</p>"

        html += "</div></div>"

    return html



def generate_combined_viewer_html(
    display_images: List[Tuple], 
    ocr_results: List[Dict], 
    extracted_data: List[Dict]
) -> str:
    """
    Generate combined HTML with PDF viewer on left and extracted data on right
    Properly scaled to fit containers
    """
    
    # Build pages HTML with percentage-based annotations
    pages_html = ""
    for page_num, img_base64, display_width, display_height in display_images:
        page_annotations = []
        for result in ocr_results:
            if result['page_num'] == page_num:
                page_annotations = result['annotations']
                break
        
        # Scale factor between OCR resolution and display resolution
        ocr_dpi = 300
        display_dpi = 150
        scale_factor = display_dpi / ocr_dpi
        
        annotations_html = ""
        for ann in page_annotations:
            # Extract bounding box from normalized format
            bbox = ann.get('bbox_normalized', {})
            left_pct = bbox.get('x', 0) * 100
            top_pct = bbox.get('y', 0) * 100
            width_pct = bbox.get('width', 0) * 100
            height_pct = bbox.get('height', 0) * 100
            
            text = ann['text'].replace('"', '&quot;').replace("'", "&#39;").replace("<", "&lt;").replace(">", "&gt;")
            
            annotations_html += f'''
            <div class="annotation-box" style="left:{left_pct}%;top:{top_pct}%;width:{width_pct}%;height:{height_pct}%;" data-text="{text}">
                <div class="tooltip">{text}</div>
            </div>
            '''
        
        # Calculate aspect ratio for responsive container
        aspect_ratio = (display_height / display_width) * 100
        
        pages_html += f'''
        <div class="pdf-page" id="page-{page_num + 1}">
            <div class="page-header">Page {page_num + 1}</div>
            <div class="page-wrapper" style="padding-bottom: {aspect_ratio}%;">
                <img src="data:image/png;base64,{img_base64}" alt="Page {page_num + 1}">
                <div class="annotations-layer">{annotations_html}</div>
            </div>
        </div>
        '''
    
    # Generate extracted data HTML
    data_html = format_extracted_data_html(extracted_data)
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            html, body {{
                height: 100%;
                overflow: hidden;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0f0f1a;
                color: #e0e0e0;
            }}
            
            .main-container {{
                display: flex;
                height: 100vh;
                overflow: hidden;
            }}
            
            /* Left Panel - PDF Viewer */
            .left-panel {{
                flex: 1;
                min-width: 0;
                background: #1a1a2e;
                display: flex;
                flex-direction: column;
                border-right: 2px solid #2a2a4a;
            }}
            
            .left-panel .panel-header {{
                flex-shrink: 0;
            }}
            
            .left-panel .panel-content {{
                flex: 1;
                overflow-y: auto;
                padding: 15px;
            }}
            
            /* Right Panel - Extracted Data */
            .right-panel {{
                width: 40%;
                min-width: 350px;
                max-width: 500px;
                background: #16213e;
                display: flex;
                flex-direction: column;
            }}
            
            .right-panel .panel-header {{
                flex-shrink: 0;
            }}
            
            .right-panel .panel-content {{
                flex: 1;
                overflow-y: auto;
                padding: 15px;
            }}
            
            .panel-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 12px 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 8px;
            }}
            
            .panel-header h2 {{
                color: white;
                font-size: 0.95rem;
                font-weight: 600;
                white-space: nowrap;
            }}
            
            .controls-group {{
                display: flex;
                gap: 6px;
                align-items: center;
                flex-wrap: wrap;
            }}
            
            .ctrl-btn {{
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                padding: 6px 10px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.2s;
            }}
            
            .ctrl-btn:hover {{ background: rgba(255,255,255,0.3); }}
            .ctrl-btn.active {{ background: rgba(255,255,255,0.4); }}
            
            .page-select {{
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                padding: 6px 8px;
                border-radius: 5px;
                font-size: 12px;
                max-width: 120px;
            }}
            
            .page-select option {{ background: #333; }}
            
            .zoom-controls {{
                display: flex;
                align-items: center;
                gap: 4px;
            }}
            
            .zoom-controls button {{
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                width: 26px;
                height: 26px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }}
            
            .zoom-level {{
                color: white;
                font-size: 11px;
                min-width: 40px;
                text-align: center;
            }}
            
            .stats-row {{
                display: flex;
                gap: 10px;
                color: white;
                font-size: 11px;
            }}
            
            .stat {{ display: flex; align-items: center; gap: 3px; }}
            .stat-val {{ font-weight: 700; }}
            
            /* PDF Pages - Responsive */
            .pages-wrapper {{
                transition: transform 0.3s ease;
                transform-origin: top center;
            }}
            
            .pdf-page {{
                background: #1e1e3a;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 15px;
            }}
            
            .page-header {{
                color: #888;
                font-size: 12px;
                margin-bottom: 10px;
                padding-bottom: 8px;
                border-bottom: 1px solid #333;
            }}
            
            /* Responsive page wrapper using aspect ratio technique */
            .page-wrapper {{
                position: relative;
                width: 100%;
                overflow: hidden;
                border-radius: 4px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4);
                background: #fff;
            }}
            
            .page-wrapper img {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                object-fit: contain;
                display: block;
            }}
            
            .annotations-layer {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
            }}
            
            .annotation-box {{
                position: absolute;
                border: 1.5px solid rgba(102,126,234,0.7);
                background: rgba(102,126,234,0.08);
                cursor: pointer;
                pointer-events: auto;
                transition: all 0.2s;
                border-radius: 2px;
            }}
            
            .annotation-box:hover {{
                background: rgba(102,126,234,0.25);
                border-color: #667eea;
                box-shadow: 0 0 10px rgba(102,126,234,0.5);
                z-index: 50;
            }}
            
            .tooltip {{
                position: absolute;
                bottom: calc(100% + 6px);
                left: 50%;
                transform: translateX(-50%);
                background: #1a1a2e;
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
                max-width: 250px;
                min-width: 80px;
                opacity: 0;
                visibility: hidden;
                transition: all 0.2s;
                z-index: 1000;
                box-shadow: 0 6px 20px rgba(0,0,0,0.6);
                border: 1px solid rgba(102,126,234,0.3);
                word-wrap: break-word;
                line-height: 1.4;
            }}
            
            .tooltip::before {{
                content: '';
                position: absolute;
                top: 100%;
                left: 50%;
                transform: translateX(-50%);
                border: 5px solid transparent;
                border-top-color: #1a1a2e;
            }}
            
            .annotation-box:hover .tooltip {{
                opacity: 1;
                visibility: visible;
            }}
            
            .annotations-hidden .annotation-box {{
                opacity: 0;
                pointer-events: none;
            }}
            
            /* Extracted Data Styles */
            .batch-card {{
                background: #1e1e3a;
                border-radius: 8px;
                margin-bottom: 12px;
                overflow: hidden;
                border: 1px solid #2a2a4a;
            }}
            
            .batch-header {{
                background: linear-gradient(135deg, #2d2d5a 0%, #1e1e3a 100%);
                padding: 10px 12px;
                display: flex;
                align-items: center;
                gap: 8px;
                border-bottom: 1px solid #3a3a6a;
                font-size: 13px;
            }}
            
            .batch-icon {{ font-size: 1rem; }}
            
            .page-badge {{
                background: rgba(102,126,234,0.3);
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 10px;
                margin-left: auto;
            }}
            
            .batch-content {{ padding: 12px; }}
            
            .section {{
                margin-bottom: 12px;
            }}
            
            .section:last-child {{ margin-bottom: 0; }}
            
            .section h4 {{
                color: #667eea;
                font-size: 12px;
                margin-bottom: 8px;
                padding-bottom: 4px;
                border-bottom: 1px solid #333;
            }}
            
            .section table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 11px;
            }}
            
            .section table th {{
                background: rgba(102,126,234,0.2);
                padding: 6px 8px;
                text-align: left;
                font-weight: 600;
            }}
            
            .section table td {{
                padding: 6px 8px;
                border-bottom: 1px solid #2a2a4a;
            }}
            
            .section table td.key {{
                color: #888;
                width: 40%;
            }}
            
            .section table tr:hover td {{
                background: rgba(102,126,234,0.1);
            }}
            
            /* Scrollbar */
            ::-webkit-scrollbar {{ width: 8px; }}
            ::-webkit-scrollbar-track {{ background: #1a1a2e; }}
            ::-webkit-scrollbar-thumb {{ background: #667eea; border-radius: 4px; }}
            ::-webkit-scrollbar-thumb:hover {{ background: #764ba2; }}
            
            /* Fit modes */
            .fit-width .page-wrapper {{
                max-width: 100%;
            }}
            
            .fit-page .pages-wrapper {{
                max-width: 800px;
                margin: 0 auto;
            }}
            .kv-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 12px;
            }}

            .kv-table td {{
                padding: 8px 10px;
                border-bottom: 1px solid #2a2a4a;
                vertical-align: top;
            }}

            .kv-table td.key {{
                width: 35%;
                color: #9aa4ff;
                font-weight: 600;
            }}

            .kv-table td.value {{
                color: #eaeaff;
                word-break: break-word;
            }}

            .sub-card {{
                background: #1b1b35;
                border: 1px solid #2a2a4a;
                border-radius: 6px;
                padding: 8px;
                margin: 8px 0;
            }}

            .sub-title {{
                font-size: 11px;
                font-weight: 700;
                color: #ffd479;
                margin-bottom: 6px;
                text-transform: uppercase;
            }}

            .inline-row {{
                display: flex;
                gap: 6px;
                margin-bottom: 4px;
            }}

            .inline-key {{
                color: #9aa4ff;
                font-weight: 600;
            }}

            .inline-value {{
                color: #eaeaff;
            }}

        </style>
    </head>
    <body>
        <div class="main-container">
            <!-- Left Panel: PDF Viewer -->
            <div class="left-panel" id="leftPanel">
                <div class="panel-header">
                    <h2>📄 PDF with Annotations</h2>
                    <div class="controls-group">
                        <button class="ctrl-btn" onclick="prevPage()">◀</button>
                        <select class="page-select" id="pageSelect" onchange="goToPage(this.value)">
                            {generate_page_options(len(display_images))}
                        </select>
                        <button class="ctrl-btn" onclick="nextPage()">▶</button>
                        <div class="zoom-controls">
                            <button onclick="zoomOut()">−</button>x
                            <span class="zoom-level" id="zoomLevel">100%</span>
                            <button onclick="zoomIn()">+</button>
                        </div>
                        <button class="ctrl-btn active" id="toggleBtn" onclick="toggleAnnotations()">👁</button>
                    </div>
                    <div class="stats-row">
                        <span class="stat">📄 <span class="stat-val">{len(display_images)}</span></span>
                        <span class="stat">📝 <span class="stat-val">{sum(len(r['annotations']) for r in ocr_results)}</span></span>
                    </div>
                </div>
                <div class="panel-content" id="pdfContent">
                    <div class="pages-wrapper" id="pagesWrapper">
                        {pages_html}
                    </div>
                </div>
            </div>
            
            <!-- Right Panel: Extracted Data -->
            <div class="right-panel">
                <div class="panel-header">
                    <h2>📊 Data Translated from Swedish to English </h2>
                    <div class="stats-row">
                        <span class="stat">📦 <span class="stat-val">{len(extracted_data)}</span> batches</span>
                    </div>
                </div>
                <div class="panel-content" id="dataContent">
                    {data_html if data_html else '<p style="color:#888;text-align:center;padding:20px;">No data extracted from API</p>'}
                </div>
            </div>
        </div>
        
        <script>
            let currentPage = 1;
            const totalPages = {len(display_images)};
            let zoomLevel = 100;
            let annotationsVisible = true;
            
            function goToPage(num) {{
                currentPage = parseInt(num);
                const el = document.getElementById('page-' + currentPage);
                if (el) {{
                    el.scrollIntoView({{behavior:'smooth', block:'start'}});
                }}
                document.getElementById('pageSelect').value = currentPage;
            }}
            
            function prevPage() {{ if(currentPage > 1) goToPage(currentPage - 1); }}
            function nextPage() {{ if(currentPage < totalPages) goToPage(currentPage + 1); }}
            
            function zoomIn() {{
                if (zoomLevel < 200) {{
                    zoomLevel += 25;
                    applyZoom();
                }}
            }}
            
            function zoomOut() {{
                if (zoomLevel > 50) {{
                    zoomLevel -= 25;
                    applyZoom();
                }}
            }}
            
            function applyZoom() {{
                const wrapper = document.getElementById('pagesWrapper');
                wrapper.style.transform = 'scale(' + (zoomLevel / 100) + ')';
                wrapper.style.transformOrigin = 'top center';
                document.getElementById('zoomLevel').textContent = zoomLevel + '%';
            }}
            
            function toggleAnnotations() {{
                annotationsVisible = !annotationsVisible;
                const wrapper = document.getElementById('pagesWrapper');
                const btn = document.getElementById('toggleBtn');
                wrapper.classList.toggle('annotations-hidden', !annotationsVisible);
                btn.classList.toggle('active', annotationsVisible);
            }}
            
            // Track scroll for current page
            document.getElementById('pdfContent').addEventListener('scroll', function() {{
                const pages = document.querySelectorAll('.pdf-page');
                const containerTop = this.getBoundingClientRect().top;
                
                pages.forEach((page, idx) => {{
                    const rect = page.getBoundingClientRect();
                    const relativeTop = rect.top - containerTop;
                    
                    if (relativeTop <= 100 && relativeTop + rect.height > 100) {{
                        currentPage = idx + 1;
                        document.getElementById('pageSelect').value = currentPage;
                    }}
                }});
            }});
            
            // Keyboard shortcuts
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'ArrowLeft') prevPage();
                if (e.key === 'ArrowRight') nextPage();
                if (e.key === '+' || e.key === '=') zoomIn();
                if (e.key === '-') zoomOut();
            }});
        </script>
    </body>
    </html>
    '''
    
    return html