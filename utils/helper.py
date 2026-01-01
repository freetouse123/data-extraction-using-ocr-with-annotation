"""
Helper functions for PDF processing, OCR normalization, and HTML generation
"""

from typing import List, Dict, Tuple
import base64


def normalize_ocr(result, img_width: int, img_height: int) -> List[Dict]:
    """
    Normalize OCR results from Azure Vision API
    
    Args:
        result: Azure Vision OCR result object
        img_width: Image width in pixels
        img_height: Image height in pixels
    
    Returns:
        List of annotation dictionaries with bounding box coordinates
    """
    annotations = []
    
    if not result or not result.read or not result.read.blocks:
        return annotations
    
    for block in result.read.blocks:
        for line in block.lines:
            text = " ".join(word.text for word in line.words)
            
            xs, ys = [], []
            for word in line.words:
                for p in word.bounding_polygon:
                    xs.append(p.x)
                    ys.append(p.y)
            
            if xs and ys:
                annotations.append({
                    "text": text,
                    "x0": min(xs),
                    "y0": min(ys),
                    "x1": max(xs),
                    "y1": max(ys),
                    "img_width": img_width,
                    "img_height": img_height
                })
    
    return annotations


def generate_page_options(total_pages: int) -> str:
    """Generate HTML options for page selector"""
    options = ""
    for i in range(1, total_pages + 1):
        options += f'<option value="{i}">Page {i} of {total_pages}</option>'
    return options


def generate_pdf_viewer_html(display_images: List[Tuple], ocr_results: List[Dict], height: int = 700) -> str:
    """
    Generate HTML viewer with annotations
    
    Args:
        display_images: List of tuples (page_num, img_base64, width, height)
        ocr_results: List of OCR result dictionaries
        height: Viewer height in pixels
    
    Returns:
        Complete HTML string for the PDF viewer
    """
    
    # Scale factor between OCR resolution and display resolution
    ocr_dpi = 300
    display_dpi = 150
    scale_factor = display_dpi / ocr_dpi
    
    # Build pages HTML
    pages_html = ""
    for page_num, img_base64, display_width, display_height in display_images:
        # Get annotations for this page
        page_annotations = []
        for result in ocr_results:
            if result['page_num'] == page_num:
                page_annotations = result['annotations']
                break
        
        # Build annotation boxes HTML
        annotations_html = ""
        for idx, ann in enumerate(page_annotations):
            # Scale coordinates from OCR resolution to display resolution
            x = ann['x0'] * scale_factor
            y = ann['y0'] * scale_factor
            width = (ann['x1'] - ann['x0']) * scale_factor
            height_box = (ann['y1'] - ann['y0']) * scale_factor
            
            # Escape text for HTML
            text = ann['text'].replace('"', '&quot;').replace("'", "&#39;").replace("<", "&lt;").replace(">", "&gt;")
            
            annotations_html += f'''
            <div class="annotation-box" 
                 style="left: {x}px; top: {y}px; width: {width}px; height: {height_box}px;"
                 data-text="{text}">
                <div class="tooltip">{text}</div>
            </div>
            '''
        
        pages_html += f'''
        <div class="pdf-page" id="page-{page_num + 1}">
            <div class="page-header">Page {page_num + 1}</div>
            <div class="page-container" style="width: {display_width}px; height: {display_height}px;">
                <img src="data:image/png;base64,{img_base64}" 
                     alt="Page {page_num + 1}" 
                     style="width: {display_width}px; height: {display_height}px;">
                <div class="annotations-layer">
                    {annotations_html}
                </div>
            </div>
        </div>
        '''
    
    # Complete HTML with CSS and JavaScript
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
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: #1a1a2e;
                padding: 10px;
            }}
            
            .viewer-container {{
                max-width: 100%;
                margin: 0 auto;
            }}
            
            .controls {{
                position: sticky;
                top: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 10px 15px;
                border-radius: 8px;
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
                gap: 10px;
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
                gap: 5px;
            }}
            
            .page-nav button {{
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.2s;
            }}
            
            .page-nav button:hover {{
                background: rgba(255, 255, 255, 0.3);
            }}
            
            .page-nav select {{
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                padding: 6px 10px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
            }}
            
            .page-nav select option {{
                background: #333;
                color: white;
            }}
            
            .toggle-btn {{
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.2s;
            }}
            
            .toggle-btn:hover {{
                background: rgba(255, 255, 255, 0.3);
            }}
            
            .toggle-btn.active {{
                background: rgba(255, 255, 255, 0.4);
            }}
            
            .pdf-page {{
                margin-bottom: 20px;
                background: #16213e;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            }}
            
            .page-header {{
                color: #a0a0a0;
                font-size: 12px;
                margin-bottom: 10px;
                padding-bottom: 8px;
                border-bottom: 1px solid #2a2a4a;
            }}
            
            .page-container {{
                position: relative;
                margin: 0 auto;
                box-shadow: 0 4px 25px rgba(0, 0, 0, 0.4);
                border-radius: 4px;
                overflow: hidden;
            }}
            
            .page-container img {{
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
                border: 2px solid rgba(102, 126, 234, 0.8);
                background: rgba(102, 126, 234, 0.1);
                cursor: pointer;
                pointer-events: auto;
                transition: all 0.2s ease;
                border-radius: 2px;
            }}
            
            .annotation-box:hover {{
                background: rgba(102, 126, 234, 0.25);
                border-color: rgba(102, 126, 234, 1);
                box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
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
                font-size: 12px;
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
            
            .zoom-controls {{
                display: flex;
                align-items: center;
                gap: 5px;
            }}
            
            .zoom-controls button {{
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                width: 28px;
                height: 28px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }}
            
            .zoom-level {{
                color: white;
                font-size: 12px;
                min-width: 40px;
                text-align: center;
            }}
            
            .stats-bar {{
                background: rgba(255, 255, 255, 0.1);
                padding: 6px 12px;
                border-radius: 6px;
                color: white;
                font-size: 11px;
                display: flex;
                gap: 15px;
            }}
            
            .stat-item {{
                display: flex;
                align-items: center;
                gap: 4px;
            }}
            
            .stat-value {{
                font-weight: 600;
            }}
            
            ::-webkit-scrollbar {{
                width: 8px;
            }}
            
            ::-webkit-scrollbar-track {{
                background: #1a1a2e;
            }}
            
            ::-webkit-scrollbar-thumb {{
                background: #667eea;
                border-radius: 4px;
            }}
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
                <div style="display: flex; gap: 8px; align-items: center;">
                    <div class="stats-bar">
                        <div class="stat-item">
                            <span>📄</span>
                            <span class="stat-value">{len(display_images)}</span>
                        </div>
                        <div class="stat-item">
                            <span>📝</span>
                            <span class="stat-value">{sum(len(r['annotations']) for r in ocr_results)}</span>
                        </div>
                    </div>
                    <button class="toggle-btn active" id="toggleAnnotations" onclick="toggleAnnotations()">
                        👁
                    </button>
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
            
            function goToPage(pageNum) {{
                currentPage = parseInt(pageNum);
                const element = document.getElementById('page-' + currentPage);
                if (element) {{
                    element.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
                document.getElementById('pageSelect').value = currentPage;
            }}
            
            function prevPage() {{
                if (currentPage > 1) goToPage(currentPage - 1);
            }}
            
            function nextPage() {{
                if (currentPage < totalPages) goToPage(currentPage + 1);
            }}
            
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
                const btn = document.getElementById('toggleAnnotations');
                
                if (annotationsVisible) {{
                    wrapper.classList.remove('annotations-hidden');
                    btn.classList.add('active');
                }} else {{
                    wrapper.classList.add('annotations-hidden');
                    btn.classList.remove('active');
                }}
            }}
        </script>
    </body>
    </html>
    '''
    
    return html


def format_extracted_data_html(extracted_data: List[Dict]) -> str:
    """
    Format extracted API data as styled HTML for display
    
    Args:
        extracted_data: List of batch data from API
    
    Returns:
        Formatted HTML string
    """
    if not extracted_data:
        return "<p>No data extracted</p>"
    
    html_parts = []
    
    for batch in extracted_data:
        batch_no = batch.get("batch_number", "N/A")
        page_range = batch.get("page_range", "N/A")
        response = batch.get("response", {})
        
        batch_html = f'''
        <div class="batch-card">
            <div class="batch-header">
                <span class="batch-icon">📦</span>
                <span>Batch {batch_no}</span>
                <span class="page-badge">Pages {page_range}</span>
            </div>
            <div class="batch-content">
        '''
        
        # Analysis Instruction
        if response.get("analysis_instruction"):
            batch_html += '<div class="section"><h4>🧪 Analysis Instruction</h4><table>'
            for key, value in response["analysis_instruction"].items():
                batch_html += f'<tr><td class="key">{key}</td><td>{value}</td></tr>'
            batch_html += '</table></div>'
        
        # Specifications
        if response.get("specifications"):
            batch_html += '<div class="section"><h4>📏 Specifications</h4><table>'
            specs = response["specifications"]
            if specs and len(specs) > 0:
                headers = list(specs[0].keys()) if isinstance(specs[0], dict) else []
                if headers:
                    batch_html += '<tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr>'
                for spec in specs:
                    if isinstance(spec, dict):
                        batch_html += '<tr>' + ''.join(f'<td>{spec.get(h, "")}</td>' for h in headers) + '</tr>'
            batch_html += '</table></div>'
        
        # Protocol Info
        if response.get("protocol_info"):
            batch_html += '<div class="section"><h4>📑 Protocol Info</h4><table>'
            for key, value in response["protocol_info"].items():
                batch_html += f'<tr><td class="key">{key}</td><td>{value}</td></tr>'
            batch_html += '</table></div>'
        
        # Instrumentation
        if response.get("instrumentation"):
            batch_html += '<div class="section"><h4>⚙️ Instrumentation</h4><table>'
            for key, val in response["instrumentation"].items():
                if isinstance(val, dict):
                    for sub_k, sub_v in val.items():
                        batch_html += f'<tr><td class="key">{key} - {sub_k}</td><td>{sub_v}</td></tr>'
                else:
                    batch_html += f'<tr><td class="key">{key}</td><td>{val}</td></tr>'
            batch_html += '</table></div>'
        
        # Reagents
        if response.get("reagents"):
            batch_html += '<div class="section"><h4>🧴 Reagents</h4><table>'
            reagents = response["reagents"]
            if reagents and len(reagents) > 0:
                headers = list(reagents[0].keys()) if isinstance(reagents[0], dict) else []
                if headers:
                    batch_html += '<tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr>'
                for reagent in reagents:
                    if isinstance(reagent, dict):
                        batch_html += '<tr>' + ''.join(f'<td>{reagent.get(h, "")}</td>' for h in headers) + '</tr>'
            batch_html += '</table></div>'
        
        # Consumables
        if response.get("consumables"):
            batch_html += '<div class="section"><h4>🧾 Consumables</h4><table>'
            consumables = response["consumables"]
            if consumables and len(consumables) > 0:
                headers = list(consumables[0].keys()) if isinstance(consumables[0], dict) else []
                if headers:
                    batch_html += '<tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr>'
                for item in consumables:
                    if isinstance(item, dict):
                        batch_html += '<tr>' + ''.join(f'<td>{item.get(h, "")}</td>' for h in headers) + '</tr>'
            batch_html += '</table></div>'
        
        # Sign-off
        if response.get("sign_off"):
            batch_html += '<div class="section"><h4>✍️ Sign-off</h4><table>'
            for key, value in response["sign_off"].items():
                batch_html += f'<tr><td class="key">{key}</td><td>{value}</td></tr>'
            batch_html += '</table></div>'
        
        batch_html += '</div></div>'
        html_parts.append(batch_html)
    
    return ''.join(html_parts)


def generate_combined_viewer_html(
    display_images: List[Tuple], 
    ocr_results: List[Dict], 
    extracted_data: List[Dict]
) -> str:
    """
    Generate combined HTML with PDF viewer on left and extracted data on right
    """
    
    # Generate PDF pages HTML
    ocr_dpi = 300
    display_dpi = 150
    scale_factor = display_dpi / ocr_dpi
    
    pages_html = ""
    for page_num, img_base64, display_width, display_height in display_images:
        page_annotations = []
        for result in ocr_results:
            if result['page_num'] == page_num:
                page_annotations = result['annotations']
                break
        
        annotations_html = ""
        for ann in page_annotations:
            x = ann['x0'] * scale_factor
            y = ann['y0'] * scale_factor
            width = (ann['x1'] - ann['x0']) * scale_factor
            height_box = (ann['y1'] - ann['y0']) * scale_factor
            text = ann['text'].replace('"', '&quot;').replace("'", "&#39;").replace("<", "&lt;").replace(">", "&gt;")
            
            annotations_html += f'''
            <div class="annotation-box" style="left:{x}px;top:{y}px;width:{width}px;height:{height_box}px;" data-text="{text}">
                <div class="tooltip">{text}</div>
            </div>
            '''
        
        pages_html += f'''
        <div class="pdf-page" id="page-{page_num + 1}">
            <div class="page-header">Page {page_num + 1}</div>
            <div class="page-container" style="width:{display_width}px;height:{display_height}px;">
                <img src="data:image/png;base64,{img_base64}" style="width:{display_width}px;height:{display_height}px;">
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
                background: #1a1a2e;
                overflow-y: auto;
                padding: 15px;
                border-right: 2px solid #2a2a4a;
            }}
            
            /* Right Panel - Extracted Data */
            .right-panel {{
                width: 45%;
                background: #16213e;
                overflow-y: auto;
                padding: 15px;
            }}
            
            .panel-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 12px 18px;
                border-radius: 10px;
                margin-bottom: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: sticky;
                top: 0;
                z-index: 100;
            }}
            
            .panel-header h2 {{
                color: white;
                font-size: 1.1rem;
                font-weight: 600;
            }}
            
            .controls-group {{
                display: flex;
                gap: 8px;
                align-items: center;
            }}
            
            .ctrl-btn {{
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
            }}
            
            .ctrl-btn:hover {{ background: rgba(255,255,255,0.3); }}
            .ctrl-btn.active {{ background: rgba(255,255,255,0.4); }}
            
            .page-select {{
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                padding: 6px 10px;
                border-radius: 6px;
                font-size: 12px;
            }}
            
            .page-select option {{ background: #333; }}
            
            /* PDF Pages */
            .pdf-page {{
                background: #1e1e3a;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
            }}
            
            .page-header {{
                color: #888;
                font-size: 12px;
                margin-bottom: 10px;
                padding-bottom: 8px;
                border-bottom: 1px solid #333;
            }}
            
            .page-container {{
                position: relative;
                margin: 0 auto;
                border-radius: 4px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            }}
            
            .page-container img {{ display: block; }}
            
            .annotations-layer {{
                position: absolute;
                top: 0; left: 0;
                width: 100%; height: 100%;
            }}
            
            .annotation-box {{
                position: absolute;
                border: 2px solid rgba(102,126,234,0.7);
                background: rgba(102,126,234,0.1);
                cursor: pointer;
                transition: all 0.2s;
                border-radius: 2px;
            }}
            
            .annotation-box:hover {{
                background: rgba(102,126,234,0.3);
                border-color: #667eea;
                box-shadow: 0 0 12px rgba(102,126,234,0.5);
                z-index: 50;
            }}
            
            .tooltip {{
                position: absolute;
                bottom: calc(100% + 8px);
                left: 50%;
                transform: translateX(-50%);
                background: #1a1a2e;
                color: white;
                padding: 10px 14px;
                border-radius: 8px;
                font-size: 12px;
                max-width: 280px;
                min-width: 100px;
                opacity: 0;
                visibility: hidden;
                transition: all 0.2s;
                z-index: 1000;
                box-shadow: 0 8px 25px rgba(0,0,0,0.6);
                border: 1px solid rgba(102,126,234,0.3);
                word-wrap: break-word;
            }}
            
            .tooltip::before {{
                content: '';
                position: absolute;
                top: 100%;
                left: 50%;
                transform: translateX(-50%);
                border: 6px solid transparent;
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
                border-radius: 10px;
                margin-bottom: 15px;
                overflow: hidden;
                border: 1px solid #2a2a4a;
            }}
            
            .batch-header {{
                background: linear-gradient(135deg, #2d2d5a 0%, #1e1e3a 100%);
                padding: 12px 15px;
                display: flex;
                align-items: center;
                gap: 10px;
                border-bottom: 1px solid #3a3a6a;
            }}
            
            .batch-icon {{ font-size: 1.2rem; }}
            
            .page-badge {{
                background: rgba(102,126,234,0.3);
                padding: 3px 10px;
                border-radius: 12px;
                font-size: 11px;
                margin-left: auto;
            }}
            
            .batch-content {{ padding: 15px; }}
            
            .section {{
                margin-bottom: 15px;
            }}
            
            .section:last-child {{ margin-bottom: 0; }}
            
            .section h4 {{
                color: #667eea;
                font-size: 13px;
                margin-bottom: 10px;
                padding-bottom: 5px;
                border-bottom: 1px solid #333;
            }}
            
            .section table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 12px;
            }}
            
            .section table th {{
                background: rgba(102,126,234,0.2);
                padding: 8px 10px;
                text-align: left;
                font-weight: 600;
            }}
            
            .section table td {{
                padding: 8px 10px;
                border-bottom: 1px solid #2a2a4a;
            }}
            
            .section table td.key {{
                color: #888;
                width: 40%;
            }}
            
            .section table tr:hover td {{
                background: rgba(102,126,234,0.1);
            }}
            
            /* Stats */
            .stats-row {{
                display: flex;
                gap: 10px;
                color: white;
                font-size: 11px;
            }}
            
            .stat {{ display: flex; align-items: center; gap: 4px; }}
            .stat-val {{ font-weight: 700; }}
            
            /* Scrollbar */
            ::-webkit-scrollbar {{ width: 8px; }}
            ::-webkit-scrollbar-track {{ background: #1a1a2e; }}
            ::-webkit-scrollbar-thumb {{ background: #667eea; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="main-container">
            <!-- Left Panel: PDF Viewer -->
            <div class="left-panel" id="leftPanel">
                <div class="panel-header">
                    <h2>📄 PDF with OCR Annotations</h2>
                    <div class="controls-group">
                        <button class="ctrl-btn" onclick="prevPage()">◀</button>
                        <select class="page-select" id="pageSelect" onchange="goToPage(this.value)">
                            {generate_page_options(len(display_images))}
                        </select>
                        <button class="ctrl-btn" onclick="nextPage()">▶</button>
                        <button class="ctrl-btn active" id="toggleBtn" onclick="toggleAnnotations()">👁</button>
                        <div class="stats-row">
                            <span class="stat">📄 <span class="stat-val">{len(display_images)}</span></span>
                            <span class="stat">📝 <span class="stat-val">{sum(len(r['annotations']) for r in ocr_results)}</span></span>
                        </div>
                    </div>
                </div>
                <div id="pagesWrapper">
                    {pages_html}
                </div>
            </div>
            
            <!-- Right Panel: Extracted Data -->
            <div class="right-panel">
                <div class="panel-header">
                    <h2>📊 Extracted Data</h2>
                    <div class="stats-row">
                        <span class="stat">📦 <span class="stat-val">{len(extracted_data)}</span> batches</span>
                    </div>
                </div>
                <div id="dataWrapper">
                    {data_html if data_html else '<p style="color:#888;text-align:center;padding:20px;">No data extracted from API</p>'}
                </div>
            </div>
        </div>
        
        <script>
            let currentPage = 1;
            const totalPages = {len(display_images)};
            let annotationsVisible = true;
            
            function goToPage(num) {{
                currentPage = parseInt(num);
                document.getElementById('page-' + currentPage)?.scrollIntoView({{behavior:'smooth',block:'start'}});
                document.getElementById('pageSelect').value = currentPage;
            }}
            
            function prevPage() {{ if(currentPage > 1) goToPage(currentPage - 1); }}
            function nextPage() {{ if(currentPage < totalPages) goToPage(currentPage + 1); }}
            
            function toggleAnnotations() {{
                annotationsVisible = !annotationsVisible;
                const wrapper = document.getElementById('pagesWrapper');
                const btn = document.getElementById('toggleBtn');
                wrapper.classList.toggle('annotations-hidden', !annotationsVisible);
                btn.classList.toggle('active', annotationsVisible);
            }}
            
            document.getElementById('leftPanel').addEventListener('scroll', function() {{
                document.querySelectorAll('.pdf-page').forEach((page, idx) => {{
                    const rect = page.getBoundingClientRect();
                    if (rect.top <= 100 && rect.bottom > 100) {{
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