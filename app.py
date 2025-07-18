from prompt_toolkit.key_binding.bindings.named_commands import previous_history
import json
from typing import List
from extraction import extract_data
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Bill Parser", page_icon="📄", layout="wide")

st.title("📄 Water Bill Data Extractor")
st.markdown("Upload your water bill PDFs to extract key information automatically.")


col1, col2 = st.columns(2)

st.session_state["uploaded_files"] = None
st.session_state["results"] = None

with col1:
    uploaded_files = st.file_uploader(
        "Upload Bills", accept_multiple_files=True, type="pdf"
    )

    file_name: List[str] = []
    bill_no: List[str] = []
    start_date: List[str] = []
    end_date: List[str] = []
    days: List[int] = []
    usage: List = []
    water: List = []
    bill_amount: List = []
    sewage: List = []

    if uploaded_files:

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, uploaded_file in enumerate(uploaded_files):

            status_text.text(f"Processing {uploaded_file.name}...")

            file_content = uploaded_file.read()
            extracted_data = extract_data(file_content)

            data = json.loads(extracted_data)

            file_name.append(uploaded_file.name)
            bill_no.append(data["bill_no"])
            start_date.append(
                f"{data['previous_date']['day']:02d}-{data['previous_date']['month']:02d}-{data['previous_date']['year']}"
            )
            end_date.append(
                f"{data['current_date']['day']:02d}-{data['current_date']['month']:02d}-{data['current_date']['year']}"
            )
            usage.append(f"{data["consumption"]} m³")
            water.append(f"{data["total_bill"]}")

            sewage_no = data["sewage"] if data["sewage"] else 0
            sewage.append(sewage_no)
            bill_amount.append(float(data["total_bill"]) + float(sewage_no))

            df = pd.DataFrame(
                {
                    "File name": file_name,
                    "Bill No": bill_no,
                    "Start Date": start_date,
                    "End Date": end_date,
                    "Usage": usage,
                    "Water": water,
                    "Sewage": sewage,
                    "Bill Amount": bill_amount,
                }
            )

            st.session_state["results"] = df

            progress_bar.progress((i + 1) / len(uploaded_files))

        # Clear status text
        status_text.empty()
        progress_bar.empty()


with col2:
    if st.session_state["results"] is not None:
        st.table(st.session_state["results"])
