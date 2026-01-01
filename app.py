import streamlit as st
import requests
import pandas as pd

st.set_page_config(
    page_title="RFP PDF Extractor",
    page_icon="📄",
    layout="centered"
)

st.title("📄 RFP Data Extractor")
st.markdown("Upload an **RFP / Tender PDF** to extract structured data automatically.")

if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None

uploaded_file = st.file_uploader(
    "Upload PDF Document",
    type=["pdf"],
    help="Only PDF files are supported"
)

# ---------------------------
# Extract button
# ---------------------------
if uploaded_file and st.button("🔍 Extract Data", width="stretch"):
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
                "http://localhost:8000/api/v1/batch-extract-data",
                files=files,
                headers={"accept": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    st.session_state.extracted_data = result["data"]
                    st.success("✅ Data extracted successfully!")
                else:
                    st.error("❌ Extraction failed")
            else:
                st.error(f"API Error: {response.status_code}")

        except Exception as e:
            st.error(f"Error: {e}")

# ---------------------------
# Display extracted data
# ---------------------------
if st.session_state.extracted_data:
    st.subheader("📊 Extracted Batches")

    for batch in st.session_state.extracted_data:
        batch_no = batch.get("batch_number", "N/A")
        page_range = batch.get("page_range", "N/A")
        response = batch.get("response", {})

        with st.expander(f"📦 Batch {batch_no} (Pages {page_range})", expanded=False):

            # -------- Analysis Instruction --------
            if response.get("analysis_instruction"):
                st.markdown("### 🧪 Analysis Instruction")
                df = pd.DataFrame(
                    response["analysis_instruction"].items(),
                    columns=["Field", "Value"]
                )
                st.dataframe(df, hide_index=True, width="stretch")

            # -------- Specifications --------
            if response.get("specifications"):
                st.markdown("### 📏 Specifications")
                st.dataframe(
                    pd.DataFrame(response["specifications"]),
                    hide_index=True,
                    width="stretch"
                )

            # -------- Protocol Info --------
            if response.get("protocol_info"):
                st.markdown("### 📑 Protocol Information")
                df = pd.DataFrame(
                    response["protocol_info"].items(),
                    columns=["Field", "Value"]
                )
                st.dataframe(df, hide_index=True, width="stretch")

            # -------- Instrumentation --------
            if response.get("instrumentation"):
                st.markdown("### ⚙️ Instrumentation")
                inst_rows = []
                for key, val in response["instrumentation"].items():
                    if isinstance(val, dict):
                        for sub_k, sub_v in val.items():
                            inst_rows.append(
                                {"Instrument": key, "Field": sub_k, "Value": sub_v}
                            )
                    else:
                        inst_rows.append(
                            {"Instrument": key, "Field": "", "Value": val}
                        )

                st.dataframe(
                    pd.DataFrame(inst_rows),
                    hide_index=True,
                    width="stretch"
                )

            # -------- Reagents --------
            if response.get("reagents"):
                st.markdown("### 🧴 Reagents")
                st.dataframe(
                    pd.DataFrame(response["reagents"]),
                    hide_index=True,
                    width="stretch"
                )

            # -------- Consumables --------
            if response.get("consumables"):
                st.markdown("### 🧾 Consumables")
                st.dataframe(
                    pd.DataFrame(response["consumables"]),
                    hide_index=True,
                    width="stretch"
                )

            # -------- Sign-off --------
            if response.get("sign_off"):
                st.markdown("### ✍️ Sign-off")
                df = pd.DataFrame(
                    response["sign_off"].items(),
                    columns=["Field", "Value"]
                )
                st.dataframe(df, hide_index=True, width="stretch")

    if st.button("🧹 Clear Data", width="stretch"):
        st.session_state.extracted_data = None
        st.rerun()

st.markdown("---")
st.caption("⚙️ Powered by FastAPI + Streamlit")
