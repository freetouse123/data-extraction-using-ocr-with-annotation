"""
Helper functions for PDF processing, OCR normalization, and HTML generation
"""

from typing import List, Dict, Tuple
import base64


def normalize_ocr(result, img_width: int, img_height: int) -> List[Dict]:
    """
    Normalize OCR results from Azure Vision API
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


def format_extracted_data_html(extracted_data: List[Dict]) -> str:
    """
    Format extracted API data as styled HTML for display
    """
    if not extracted_data:
        return "<p style='color:#888;text-align:center;padding:20px;'>No data extracted</p>"
    
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
            # Get OCR dimensions
            ocr_width = ann.get('img_width', display_width / scale_factor)
            ocr_height = ann.get('img_height', display_height / scale_factor)
            
            # Convert to percentages for responsive scaling
            left_pct = (ann['x0'] / ocr_width) * 100
            top_pct = (ann['y0'] / ocr_height) * 100
            width_pct = ((ann['x1'] - ann['x0']) / ocr_width) * 100
            height_pct = ((ann['y1'] - ann['y0']) / ocr_height) * 100
            
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
                            <button onclick="zoomOut()">−</button>
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
                    <h2>📊 Extracted Data</h2>
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