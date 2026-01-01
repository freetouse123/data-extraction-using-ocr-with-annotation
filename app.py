"""
Unified Streamlit Application
PDF OCR Annotation Viewer + RFP Data Extractor
"""

import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv

from src.image_data_extraction import Pdf2ImageDataExtractor, BatchProcessor
from utils.helper import generate_pdf_viewer_html

load_dotenv()

# ==========================
# PAGE CONFIG
# ==========================
st.set_page_config(
    page_title="PDF Processing Suite",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================
# CUSTOM CSS
# ==========================
st.markdown("""
    <style>
    .main {
        padding: 1rem;
    }
    .stButton button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        padding: 0.75rem 2rem;
        border-radius: 10px;
        border: none;
        font-size: 1.1rem;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    h1 {
        color: #1a1a2e;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        color: #6c757d;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    iframe {
        border: none;
        border-radius: 12px;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================
# SIDEBAR NAVIGATION
# ==========================
st.sidebar.title("📄 PDF Processing Suite")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Select Tool",
    ["🔍 OCR Annotation Viewer", "📊 RFP Data Extractor"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    """
    **OCR Viewer**: Extract and visualize text from scanned PDFs with interactive hover annotations.
    
    **RFP Extractor**: Extract structured data from RFP/Tender documents using AI.
    """
)

# ==========================
# OCR ANNOTATION VIEWER PAGE
# ==========================
def ocr_viewer_page():
    st.title("🔍 PDF OCR Annotation Viewer")
    st.markdown(
        '<p class="subtitle">Upload a PDF to extract and visualize text with interactive hover annotations</p>',
        unsafe_allow_html=True
    )
    
    # Check environment variables
    if not os.getenv("VISION_ENDPOINT") or not os.getenv("VISION_KEY"):
        st.error("❌ Please set VISION_ENDPOINT and VISION_KEY environment variables")
        st.stop()
    
    # Initialize session state
    if 'ocr_viewer_html' not in st.session_state:
        st.session_state.ocr_viewer_html = None
        st.session_state.ocr_processing_stats = None
        st.session_state.ocr_all_annotations = []
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload a scanned or digital PDF document",
        key="ocr_uploader"
    )
    
    if uploaded_file:
        pdf_bytes = uploaded_file.read()
        
        # Show process button if not processed
        if st.session_state.ocr_viewer_html is None:
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                if st.button("🚀 Extract Text & Create Interactive Viewer", type="primary", key="ocr_process"):
                    try:
                        extractor = Pdf2ImageDataExtractor()
                        batch_processor = BatchProcessor(extractor, batch_size=5)
                        
                        # Progress tracking
                        progress_placeholder = st.empty()
                        
                        with progress_placeholder.container():
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            start_time = time.time()
                            
                            # Step 1: Convert to images for OCR
                            status_text.markdown("**📄 Converting PDF to images for OCR...**")
                            images_for_ocr = extractor.pdf_to_images_for_ocr(pdf_bytes)
                            progress_bar.progress(0.2)
                            
                            # Step 2: OCR Processing
                            status_text.markdown(f"**🔍 Processing {len(images_for_ocr)} pages with Azure OCR...**")
                            
                            def update_progress(progress):
                                progress_bar.progress(0.2 + progress * 0.4)
                            
                            all_results = batch_processor.process_all_batches(
                                images_for_ocr,
                                progress_callback=update_progress
                            )
                            progress_bar.progress(0.6)
                            
                            # Step 3: Convert to display images
                            status_text.markdown("**🖼️ Preparing display images...**")
                            display_images = extractor.pdf_to_images_for_display(pdf_bytes)
                            progress_bar.progress(0.8)
                            
                            # Step 4: Generate HTML viewer
                            status_text.markdown("**✨ Building interactive viewer...**")
                            viewer_html = generate_pdf_viewer_html(display_images, all_results)
                            progress_bar.progress(1.0)
                            
                            end_time = time.time()
                            processing_time = end_time - start_time
                            
                            status_text.markdown("**✅ Processing complete!**")
                            time.sleep(0.5)
                        
                        # Clear progress
                        progress_placeholder.empty()
                        
                        # Store results
                        st.session_state.ocr_viewer_html = viewer_html
                        st.session_state.ocr_all_annotations = all_results
                        st.session_state.ocr_processing_stats = {
                            'pages': len(all_results),
                            'annotations': sum(len(r['annotations']) for r in all_results),
                            'time': processing_time
                        }
                        
                        st.success("✅ Interactive viewer created!")
                        time.sleep(0.5)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error processing PDF: {str(e)}")
        
        # Display viewer
        if st.session_state.ocr_viewer_html:
            # Stats
            if st.session_state.ocr_processing_stats:
                stats = st.session_state.ocr_processing_stats
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("📄 Pages", stats['pages'])
                with col2:
                    st.metric("📝 Text Regions", stats['annotations'])
                with col3:
                    st.metric("⚡ Time", f"{stats['time']:.1f}s")
                with col4:
                    st.metric("📊 Speed", f"{stats['time']/stats['pages']:.2f}s/pg")
                with col5:
                    if st.button("🔄 New PDF", key="ocr_reset"):
                        st.session_state.ocr_viewer_html = None
                        st.session_state.ocr_processing_stats = None
                        st.session_state.ocr_all_annotations = []
                        st.rerun()
            
            st.markdown("---")
            st.info("💡 **Hover over blue boxes** to see detected text. Use controls to navigate, zoom, or toggle annotations.")
            
            # Render HTML viewer
            components.html(
                st.session_state.ocr_viewer_html,
                height=900,
                scrolling=True
            )
            
            # Download extracted text
            st.markdown("---")
            col_a, col_b, col_c = st.columns([1, 1, 1])
            
            with col_b:
                all_text = ""
                for result in st.session_state.ocr_all_annotations:
                    all_text += f"\n{'='*50}\nPage {result['page_num'] + 1}\n{'='*50}\n\n"
                    for ann in result['annotations']:
                        all_text += f"{ann['text']}\n"
                
                st.download_button(
                    label="📥 Download Extracted Text",
                    data=all_text,
                    file_name="extracted_text.txt",
                    mime="text/plain",
                    use_container_width=True
                )


# ==========================
# RFP DATA EXTRACTOR PAGE
# ==========================
def rfp_extractor_page():
    st.title("📊 RFP Data Extractor")
    st.markdown(
        '<p class="subtitle">Upload an RFP/Tender PDF to extract structured data automatically</p>',
        unsafe_allow_html=True
    )
    
    # Initialize session state
    if "rfp_extracted_data" not in st.session_state:
        st.session_state.rfp_extracted_data = None
    
    # API endpoint configuration
    with st.sidebar:
        st.markdown("### API Configuration")
        api_url = st.text_input(
            "API Endpoint",
            value="http://localhost:8000/api/v1/batch-extract-data",
            help="Backend API endpoint for data extraction"
        )
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload PDF Document",
        type=["pdf"],
        help="Only PDF files are supported",
        key="rfp_uploader"
    )
    
    # Extract button
    if uploaded_file:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🔍 Extract Data", type="primary", key="rfp_extract"):
                with st.spinner("Extracting data from PDF..."):
                    try:
                        files = {
                            "pdf": (
                                uploaded_file.name,
                                uploaded_file,
                                "application/pdf"
                            )
                        }
                        
                        response = requests.post(
                            api_url,
                            files=files,
                            headers={"accept": "application/json"},
                            timeout=300
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result.get("status") == "success":
                                st.session_state.rfp_extracted_data = result["data"]
                                st.success("✅ Data extracted successfully!")
                            else:
                                st.error("❌ Extraction failed: " + result.get("message", "Unknown error"))
                        else:
                            st.error(f"❌ API Error: {response.status_code} - {response.text}")
                    
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Could not connect to API. Make sure the backend server is running.")
                    except requests.exceptions.Timeout:
                        st.error("❌ Request timed out. The PDF might be too large.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    # Display extracted data
    if st.session_state.rfp_extracted_data:
        st.markdown("---")
        st.subheader("📊 Extracted Batches")
        
        for batch in st.session_state.rfp_extracted_data:
            batch_no = batch.get("batch_number", "N/A")
            page_range = batch.get("page_range", "N/A")
            response = batch.get("response", {})
            
            with st.expander(f"📦 Batch {batch_no} (Pages {page_range})", expanded=False):
                
                # Analysis Instruction
                if response.get("analysis_instruction"):
                    st.markdown("### 🧪 Analysis Instruction")
                    df = pd.DataFrame(
                        response["analysis_instruction"].items(),
                        columns=["Field", "Value"]
                    )
                    st.dataframe(df, hide_index=True, use_container_width=True)
                
                # Specifications
                if response.get("specifications"):
                    st.markdown("### 📏 Specifications")
                    st.dataframe(
                        pd.DataFrame(response["specifications"]),
                        hide_index=True,
                        use_container_width=True
                    )
                
                # Protocol Info
                if response.get("protocol_info"):
                    st.markdown("### 📑 Protocol Information")
                    df = pd.DataFrame(
                        response["protocol_info"].items(),
                        columns=["Field", "Value"]
                    )
                    st.dataframe(df, hide_index=True, use_container_width=True)
                
                # Instrumentation
                if response.get("instrumentation"):
                    st.markdown("### ⚙️ Instrumentation")
                    inst_rows = []
                    for key, val in response["instrumentation"].items():
                        if isinstance(val, dict):
                            for sub_k, sub_v in val.items():
                                inst_rows.append({
                                    "Instrument": key,
                                    "Field": sub_k,
                                    "Value": sub_v
                                })
                        else:
                            inst_rows.append({
                                "Instrument": key,
                                "Field": "",
                                "Value": val
                            })
                    
                    st.dataframe(
                        pd.DataFrame(inst_rows),
                        hide_index=True,
                        use_container_width=True
                    )
                
                # Reagents
                if response.get("reagents"):
                    st.markdown("### 🧴 Reagents")
                    st.dataframe(
                        pd.DataFrame(response["reagents"]),
                        hide_index=True,
                        use_container_width=True
                    )
                
                # Consumables
                if response.get("consumables"):
                    st.markdown("### 🧾 Consumables")
                    st.dataframe(
                        pd.DataFrame(response["consumables"]),
                        hide_index=True,
                        use_container_width=True
                    )
                
                # Sign-off
                if response.get("sign_off"):
                    st.markdown("### ✍️ Sign-off")
                    df = pd.DataFrame(
                        response["sign_off"].items(),
                        columns=["Field", "Value"]
                    )
                    st.dataframe(df, hide_index=True, use_container_width=True)
        
        # Clear data button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🧹 Clear Data", use_container_width=True, key="rfp_clear"):
                st.session_state.rfp_extracted_data = None
                st.rerun()


# ==========================
# MAIN ROUTING
# ==========================
def main():
    if page == "🔍 OCR Annotation Viewer":
        ocr_viewer_page()
    elif page == "📊 RFP Data Extractor":
        rfp_extractor_page()


if __name__ == "__main__":
    main()