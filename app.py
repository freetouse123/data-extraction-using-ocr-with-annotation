"""
Unified Streamlit Application
PDF OCR Annotation Viewer + RFP Data Extractor (Parallel Processing)
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import time
import os
import json
from dotenv import load_dotenv

from src.image_data_extraction import (
    Pdf2ImageDataExtractor, 
    BatchProcessor, 
    APIDataExtractor, 
    ParallelProcessor,
    ProgressTracker
)
from utils.helper import generate_pdf_viewer_html, generate_combined_viewer_html

load_dotenv()

# ==========================
# PAGE CONFIG
# ==========================
st.set_page_config(
    page_title="Alembic Handwritten Fields Extraction ",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================
# CUSTOM CSS
# ==========================
st.markdown("""
    <style>
    .main { padding: 0.5rem; }
    
    .stButton button {
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
    
    h1 { color: #1a1a2e; font-weight: 700; }
    
    .subtitle {
        color: #6c757d;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }
    
    iframe { border: none; border-radius: 12px; }
    
    .status-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .progress-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
    }
    
    .progress-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================
# SIDEBAR
# ==========================
st.sidebar.title("📄 Alembic Handwritten Fields Extraction ")
st.sidebar.markdown("---")

# Language Selection
st.sidebar.markdown("### 🌐 Language")
language = st.sidebar.toggle(
    "Swedish",
    value=False,
    help="Toggle between English and Swedish"
)
selected_language = "Swedish" if language else "English"
st.sidebar.info(f"Selected: **{selected_language}**")

st.sidebar.markdown("---")

# API Configuration
st.sidebar.markdown("### ⚙️ Configuration")
api_url = st.sidebar.text_input(
    "API Endpoint",
    value="http://localhost:8000/api/v1/batch-extract-data",
    help="Backend API endpoint for structured data extraction"
)

batch_size = st.sidebar.slider(
    "OCR Batch Size",
    min_value=1,
    max_value=10,
    value=5,
    help="Number of pages to process in each OCR batch"
)

use_parallel = st.sidebar.checkbox(
    "Enable Parallel Processing",
    value=True,
    help="Process OCR and API extraction simultaneously"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 About")
st.sidebar.info(
    """
    This tool processes PDFs with:
    
    1. **OCR Annotations**: Extracts text with bounding boxes using Azure Vision
    2. **API Extraction**: Sends PDF to backend API for structured data
    
    Both processes can run simultaneously for faster results!
    """
)


# ==========================
# HELPER FUNCTION FOR POLLING PROGRESS
# ==========================
def process_with_progress(
    pdf_bytes: bytes,
    filename: str,
    language: str,
    parallel_processor: ParallelProcessor,
    use_parallel: bool,
    progress_tracker: ProgressTracker
):
    """
    Run processing in a separate thread and return results
    """
    import threading
    
    result_holder = [None]
    error_holder = [None]
    
    def run_processing():
        try:
            if use_parallel:
                result_holder[0] = parallel_processor.process_pdf_parallel(
                    pdf_bytes=pdf_bytes,
                    filename=filename,
                    language=language,
                    progress_tracker=progress_tracker
                )
            else:
                result_holder[0] = parallel_processor.process_pdf_sequential(
                    pdf_bytes=pdf_bytes,
                    filename=filename,
                    language=language
                )
        except Exception as e:
            error_holder[0] = str(e)
    
    # Start processing thread
    process_thread = threading.Thread(target=run_processing)
    process_thread.start()
    
    return process_thread, result_holder, error_holder


# ==========================
# MAIN APP
# ==========================
def main():
    st.title("📄 Alembic Handwritten Fields Extraction ")
    st.markdown(
        '<p class="subtitle">Upload a PDF For extraction of the Handwritten Fields using the OCR</p>',
        unsafe_allow_html=True
    )
    
    # Check environment variables
    vision_configured = os.getenv("VISION_ENDPOINT") and os.getenv("VISION_KEY")
    
    if not vision_configured:
        st.warning("⚠️ Azure Vision API not configured. OCR annotations will not work. Set VISION_ENDPOINT and VISION_KEY environment variables.")
    
    # Initialize session state
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
        st.session_state.combined_html = None
        st.session_state.ocr_results = []
        st.session_state.api_results = {"success": False, "data": {}, "error": None}
        st.session_state.display_images = []
        st.session_state.timing = {}
        st.session_state.pdf_filename = None
        st.session_state.is_processing = False
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload a PDF document for processing",
        key="pdf_uploader"
    )
    
    if uploaded_file:
        # Check if it's a new file
        if st.session_state.pdf_filename != uploaded_file.name:
            st.session_state.processing_complete = False
            st.session_state.pdf_filename = uploaded_file.name
            st.session_state.is_processing = False
        
        pdf_bytes = uploaded_file.read()
        
        # Show file info
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.success(f"📁 **{uploaded_file.name}** ({len(pdf_bytes) / 1024:.1f} KB)")
        with col2:
            st.info(f"🌐 Language: **{selected_language}**")
        
        # Process button
        if not st.session_state.processing_complete and not st.session_state.is_processing:
            st.markdown("---")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                process_btn = st.button(
                    "🚀 Extract Text & Data",
                    type="primary",
                    use_container_width=True
                )
            
            if process_btn:
                st.session_state.is_processing = True
                st.rerun()
        
        # Processing state
        if st.session_state.is_processing and not st.session_state.processing_complete:
            st.markdown("---")
            st.markdown("### ⏳ Processing PDF...")
            
            # Create progress tracker
            progress_tracker = ProgressTracker()
            
            # Create progress display
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔍 OCR Annotation Pipeline**")
                ocr_progress_bar = st.progress(0)
                ocr_status_text = st.empty()
            
            with col2:
                st.markdown("**📊 API Data Extraction**")
                api_progress_bar = st.progress(0)
                api_status_text = st.empty()
            
            try:
                # Initialize processors
                if vision_configured:
                    extractor = Pdf2ImageDataExtractor()
                    api_extractor = APIDataExtractor(api_url=api_url)
                    parallel_processor = ParallelProcessor(
                        extractor=extractor,
                        api_extractor=api_extractor,
                        batch_size=batch_size
                    )
                    
                    # Start processing in thread
                    process_thread, result_holder, error_holder = process_with_progress(
                        pdf_bytes=pdf_bytes,
                        filename=uploaded_file.name,
                        language=selected_language,
                        parallel_processor=parallel_processor,
                        use_parallel=use_parallel,
                        progress_tracker=progress_tracker
                    )
                    
                    # Poll progress while processing
                    while process_thread.is_alive():
                        progress = progress_tracker.get_progress()
                        
                        ocr_progress_bar.progress(progress["ocr_progress"])
                        ocr_status_text.caption(progress["ocr_status"])
                        
                        api_progress_bar.progress(progress["api_progress"])
                        api_status_text.caption(progress["api_status"])
                        
                        time.sleep(0.1)
                    
                    # Wait for thread to complete
                    process_thread.join()
                    
                    # Final progress update
                    final_progress = progress_tracker.get_progress()
                    ocr_progress_bar.progress(1.0)
                    ocr_status_text.caption("✅ " + final_progress["ocr_status"])
                    api_progress_bar.progress(1.0)
                    api_status_text.caption("✅ " + final_progress["api_status"])
                    
                    # Check for errors
                    if error_holder[0]:
                        st.error(f"❌ Processing error: {error_holder[0]}")
                        st.session_state.is_processing = False
                        st.stop()
                    
                    # Get results
                    results = result_holder[0]
                    
                    if results:
                        st.session_state.ocr_results = results.get("ocr_results", [])
                        st.session_state.api_results = results.get("api_results", {})
                        st.session_state.display_images = results.get("display_images", [])
                        st.session_state.timing = results.get("timing", {})
                        
                        # Generate combined HTML
                        if st.session_state.display_images and st.session_state.ocr_results:
                            st.session_state.combined_html = generate_combined_viewer_html(
                                st.session_state.display_images,
                                st.session_state.ocr_results,
                                st.session_state.api_results.get("data", {})
                            )
                
                else:
                    # Only API extraction if Vision not configured
                    api_extractor = APIDataExtractor(api_url=api_url)
                    
                    api_status_text.caption("Sending to API...")
                    api_progress_bar.progress(0.3)
                    
                    api_result = api_extractor.extract_data(
                        pdf_bytes, 
                        language=selected_language,
                        filename=uploaded_file.name
                    )
                    
                    api_progress_bar.progress(1.0)
                    api_status_text.caption("✅ Complete!")
                    ocr_progress_bar.progress(1.0)
                    ocr_status_text.caption("⚠️ Skipped (Vision not configured)")
                    
                    st.session_state.api_results = api_result
                    st.session_state.ocr_results = []
                    st.session_state.display_images = []
                    st.session_state.timing = {"api": 0, "total": 0}
                
                st.session_state.processing_complete = True
                st.session_state.is_processing = False
                
                time.sleep(0.5)
                st.rerun()
            
            except Exception as e:
                st.error(f"❌ Error during processing: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
                st.session_state.is_processing = False
        
        # Display results
        if st.session_state.processing_complete:
            # Stats row
            st.markdown("---")
            
            timing = st.session_state.timing
            ocr_results = st.session_state.ocr_results
            api_results = st.session_state.api_results
            
            # Metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("📄 Pages", len(st.session_state.display_images) if st.session_state.display_images else 0)
            
            with col2:
                total_annotations = sum(len(r['annotations']) for r in ocr_results) if ocr_results else 0
                st.metric("📝 Annotations", total_annotations)
            
            with col3:
                st.metric("⚡ OCR Time", f"{timing.get('ocr', 0):.1f}s")
            
            with col4:
                api_time = api_results.get("processing_time", timing.get('api', 0))
                st.metric("🌐 API Time", f"{api_time:.1f}s")
            
            with col5:
                if st.button("🔄 New PDF"):
                    st.session_state.processing_complete = False
                    st.session_state.combined_html = None
                    st.session_state.ocr_results = []
                    st.session_state.api_results = {"success": False, "data": {}, "error": None}
                    st.session_state.display_images = []
                    st.session_state.timing = {}
                    st.session_state.pdf_filename = None
                    st.session_state.is_processing = False
                    st.rerun()
            
            # Status messages
            if api_results.get("error"):
                st.warning(f"⚠️ API Extraction: {api_results['error']}")
            
            if api_results.get("success"):
                detected_lang = api_results.get("language", "unknown")
                st.success(f"✅ API extraction successful! (Detected language: {detected_lang})")
            
            st.markdown("---")
            
            # Display mode selection
            display_mode = st.radio(
                "Display Mode",
                ["🔀 Combined View (Side by Side)", "📄 PDF Viewer Only", "📊 Extracted Data Only"],
                horizontal=True
            )
            
            st.markdown("---")
            
            if display_mode == "🔀 Combined View (Side by Side)":
                if st.session_state.combined_html:
                    st.info("💡 **Left**: PDF with hover annotations | **Right**: Extracted structured data")
                    components.html(
                        st.session_state.combined_html,
                        height=850,
                        scrolling=True
                    )
                elif st.session_state.display_images:
                    # Generate on the fly if not available
                    combined_html = generate_combined_viewer_html(
                        st.session_state.display_images,
                        st.session_state.ocr_results,
                        st.session_state.api_results.get("data", {})
                    )
                    components.html(combined_html, height=850, scrolling=True)
                else:
                    st.warning("Combined view not available. Showing data separately.")
                    display_mode = "📊 Extracted Data Only"
            
            if display_mode == "📄 PDF Viewer Only":
                if st.session_state.display_images and st.session_state.ocr_results:
                    viewer_html = generate_pdf_viewer_html(
                        st.session_state.display_images,
                        st.session_state.ocr_results
                    )
                    st.info("💡 **Hover over blue boxes** to see detected text")
                    components.html(viewer_html, height=850, scrolling=True)
                else:
                    st.warning("PDF viewer not available. Azure Vision API might not be configured.")
            
            if display_mode == "📊 Extracted Data Only":
                display_extracted_data(api_results)
            
            # Download section
            st.markdown("---")
            st.markdown("### 📥 Downloads")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if ocr_results:
                    all_text = ""
                    for result in ocr_results:
                        all_text += f"\n{'='*50}\nPage {result['page_num'] + 1}\n{'='*50}\n\n"
                        for ann in result['annotations']:
                            all_text += f"{ann['text']}\n"
                    
                    st.download_button(
                        label="📄 Download OCR Text",
                        data=all_text,
                        file_name="ocr_extracted_text.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
            
            with col2:
                if api_results.get("data"):
                    json_data = json.dumps(api_results["data"], indent=2, ensure_ascii=False)
                    st.download_button(
                        label="📊 Download API Data (JSON)",
                        data=json_data,
                        file_name="extracted_data.json",
                        mime="application/json",
                        use_container_width=True
                    )
            
            with col3:
                if st.session_state.combined_html:
                    st.download_button(
                        label="🌐 Download HTML Viewer",
                        data=st.session_state.combined_html,
                        file_name="pdf_viewer.html",
                        mime="text/html",
                        use_container_width=True
                    )


def display_extracted_data(api_results: dict):
    """Display extracted data from API in a structured format (non-batch)"""
    
    data = api_results.get("data", {})
    
    if not data:
        st.info("No structured data extracted from API")
        return
    
    # Show metadata if available
    metadata = data.get("_metadata", {})
    if metadata:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 Pages Processed", metadata.get("total_pages_processed", "N/A"))
        with col2:
            st.metric("✅ Processing Complete", "Yes" if metadata.get("processing_complete") else "No")
        with col3:
            st.metric("🌐 Language", api_results.get("language", "N/A"))
    
    st.markdown("---")
    
    # Analysis Instruction
    if data.get("analysis_instruction"):
        with st.expander("🧪 Analysis Instruction", expanded=True):
            df = pd.DataFrame(
                [(k, v) for k, v in data["analysis_instruction"].items() if v is not None],
                columns=["Field", "Value"]
            )
            st.dataframe(df, hide_index=True, use_container_width=True)
    
    # Protocol Header
    if data.get("protocol_header"):
        with st.expander("📑 Protocol Header", expanded=True):
            protocol = data["protocol_header"]
            
            # Basic info
            basic_info = {k: v for k, v in protocol.items() if k != "instruments" and v is not None}
            if basic_info:
                st.markdown("##### Basic Information")
                df = pd.DataFrame(
                    list(basic_info.items()),
                    columns=["Field", "Value"]
                )
                st.dataframe(df, hide_index=True, use_container_width=True)
            
            # Instruments
            instruments = protocol.get("instruments", {})
            if instruments:
                st.markdown("##### ⚙️ Instruments")
                inst_rows = [(k, v) for k, v in instruments.items() if v is not None]
                if inst_rows:
                    df = pd.DataFrame(inst_rows, columns=["Instrument", "Value"])
                    st.dataframe(df, hide_index=True, use_container_width=True)
    
    # Reagents
    if data.get("reagents"):
        with st.expander("🧴 Reagents", expanded=False):
            reagents = data["reagents"]
            for reagent_key, reagent_data in reagents.items():
                if reagent_data:
                    reagent_id = reagent_data.get("reagent_id", "")
                    reagent_name = reagent_data.get("name", reagent_key)
                    st.markdown(f"**{reagent_id}. {reagent_name}**")
                    
                    # Filter out None values and display
                    reagent_info = {k: v for k, v in reagent_data.items() if v is not None and k not in ["reagent_id", "name"]}
                    if reagent_info:
                        df = pd.DataFrame(list(reagent_info.items()), columns=["Field", "Value"])
                        st.dataframe(df, hide_index=True, use_container_width=True)
                    st.markdown("---")
    
    # Preparation Records
    if data.get("preparation_records"):
        with st.expander("📝 Preparation Records", expanded=False):
            prep_records = data["preparation_records"]
            for prep_key, prep_data in prep_records.items():
                if prep_data:
                    st.markdown(f"**{prep_key.replace('_', ' ').title()}**")
                    display_nested_dict(prep_data)
                    st.markdown("---")
    
    # Standards
    if data.get("standards"):
        with st.expander("📏 Standards", expanded=False):
            standards = data["standards"]
            for std_key, std_data in standards.items():
                if std_data:
                    st.markdown(f"**{std_key.replace('_', ' ').title()}**")
                    display_nested_dict(std_data)
                    st.markdown("---")
    
    # Test Solutions
    if data.get("test_solutions"):
        with st.expander("🧪 Test Solutions", expanded=False):
            test_solutions = data["test_solutions"]
            for sol_key, sol_data in test_solutions.items():
                if sol_data:
                    st.markdown(f"**{sol_key.replace('_', ' ').title()}**")
                    if isinstance(sol_data, list):
                        if sol_data:
                            st.dataframe(pd.DataFrame(sol_data), hide_index=True, use_container_width=True)
                        else:
                            st.caption("No data")
                    else:
                        display_nested_dict(sol_data)
    
    # System Suitability Test
    if data.get("system_suitability_test"):
        with st.expander("✅ System Suitability Test", expanded=False):
            sst = data["system_suitability_test"]
            for sst_key, sst_data in sst.items():
                if sst_data and isinstance(sst_data, dict):
                    criterion_name = sst_data.get("criterion_name", sst_key.replace('_', ' ').title())
                    st.markdown(f"**{criterion_name}**")
                    sst_info = {k: v for k, v in sst_data.items() if v is not None and k != "criterion_name"}
                    if sst_info:
                        df = pd.DataFrame(list(sst_info.items()), columns=["Field", "Value"])
                        st.dataframe(df, hide_index=True, use_container_width=True)
                elif sst_data is not None:
                    st.write(f"**{sst_key}**: {sst_data}")
    
    # Traceability
    if data.get("traceability"):
        with st.expander("🔍 Traceability", expanded=False):
            trace = data["traceability"]
            trace_info = {k: v for k, v in trace.items() if v is not None}
            if trace_info:
                # Handle list values
                for k, v in trace_info.items():
                    if isinstance(v, list):
                        trace_info[k] = ", ".join(str(x) for x in v)
                df = pd.DataFrame(list(trace_info.items()), columns=["Field", "Value"])
                st.dataframe(df, hide_index=True, use_container_width=True)


def display_nested_dict(data: dict, level: int = 0):
    """Helper function to display nested dictionaries"""
    simple_items = {}
    complex_items = {}
    
    for k, v in data.items():
        if v is None:
            continue
        if isinstance(v, dict):
            complex_items[k] = v
        elif isinstance(v, list):
            if v and isinstance(v[0], dict):
                complex_items[k] = v
            else:
                simple_items[k] = ", ".join(str(x) for x in v) if v else ""
        else:
            simple_items[k] = v
    
    # Display simple items as table
    if simple_items:
        df = pd.DataFrame(list(simple_items.items()), columns=["Field", "Value"])
        st.dataframe(df, hide_index=True, use_container_width=True)
    
    # Display complex items
    for k, v in complex_items.items():
        st.markdown(f"*{k.replace('_', ' ').title()}:*")
        if isinstance(v, dict):
            display_nested_dict(v, level + 1)
        elif isinstance(v, list):
            st.dataframe(pd.DataFrame(v), hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()