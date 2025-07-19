import requests
import json
from typing import List
import streamlit as st
import pandas as pd
import os

# API configuration
API_URL = os.environ["API_URL"]

st.set_page_config(page_title="Bill Parser", page_icon="📄", layout="wide")
st.title("📄 Water Bill Data Extractor")
st.markdown("Upload your water bill PDFs to extract key information automatically.")

col1, col2 = st.columns(2)

with col1:
    uploaded_files = st.file_uploader(
        "Upload Bills", accept_multiple_files=True, type="pdf"
    )

    if uploaded_files:
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Prepare files for API call
        files = []
        for uploaded_file in uploaded_files:
            files.append(
                ("bills", (uploaded_file.name, uploaded_file.read(), "application/pdf"))
            )

        try:
            # Call the API
            status_text.text("Processing all files...")
            response = requests.post(
                API_URL, files=files, params={"mode": "single"}  # or "merged"
            )

            if response.status_code == 200:
                api_results = response.json()["results"]

                print(api_results)

                # Process results
                file_name = []
                bill_no = []
                start_date = []
                end_date = []
                usage = []
                water = []
                sewage = []
                bill_amount = []

                for i, (uploaded_file, result) in enumerate(
                    zip(uploaded_files, api_results)
                ):

                    data = json.loads(result)

                    file_name.append(uploaded_file.name)
                    bill_no.append(data["bill_no"])
                    start_date.append(
                        f"{data['previous_date']['day']:02d}-{data['previous_date']['month']:02d}-{data['previous_date']['year']}"
                    )
                    end_date.append(
                        f"{data['current_date']['day']:02d}-{data['current_date']['month']:02d}-{data['current_date']['year']}"
                    )
                    usage.append(f"{data['consumption']} m³")
                    water.append(f"{data['total_bill']}")

                    sewage_no = data["sewage"] if data["sewage"] else 0
                    sewage.append(sewage_no)
                    bill_amount.append(float(data["total_bill"]) + float(sewage_no))

                    progress_bar.progress((i + 1) / len(uploaded_files))

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
                status_text.text("✅ Processing complete!")

            else:
                st.error(f"API Error: {response.status_code} - {response.text}")

        except requests.exceptions.ConnectionError:
            st.error(
                "❌ Cannot connect to API. Make sure the FastAPI server is running."
            )
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
        finally:
            progress_bar.empty()
            status_text.empty()

with col2:
    if st.session_state.get("results") is not None:
        st.table(st.session_state["results"])
