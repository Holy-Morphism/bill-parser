import requests
import json
from typing import List
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import base64
from io import BytesIO

# Load environment variables from .env file
load_dotenv()

# API configuration
API_URL = os.environ["API_URL"]

st.set_page_config(page_title="Bill Parser", page_icon="📄", layout="wide")
st.title("📄 Water Bill Data Extractor")
st.markdown("Upload your water bill PDFs to extract key information automatically.")

# Single column layout
uploaded_files = st.file_uploader(
    "Upload Bills", accept_multiple_files=True, type="pdf"
)

if uploaded_files:


    # Prepare files for API call
    files = []
    for uploaded_file in uploaded_files:
        files.append(
            ("bills", (uploaded_file.name, uploaded_file.read(), "application/pdf"))
        )

    # Call the API
    response = requests.post(
        API_URL, files=files, params={"mode": "single"}  # or "merged"
    )

    api_results = response.json()["bills"]

    # Print results without image data for debugging
    for i, result in enumerate(api_results):
        result_copy = result.copy()
        if "image" in result_copy:
            result_copy["image"] = (
                "[BASE64_IMAGE_DATA]" if result_copy["image"] else None
            )
        print(f"Bill {i+1}:", result_copy)

    # Process and display results one by one as expanders
    for i, data in enumerate( api_results):
      

        # Format dates
        start_date = f"{data['start_date']['day']:02d}-{data['start_date']['month']:02d}-{data['start_date']['year']}"
        end_date = f"{data['end_date']['day']:02d}-{data['end_date']['month']:02d}-{data['end_date']['year']}"
        usage = f"{data['usage']} m³"
        water = f"{data['water']}"
        sewage = data["sewage"] if data["sewage"] else 0
        bill_amount = data["bill_amount"]

        # Create expander for this bill
        with st.expander(f"📄 {uploaded_file.name} - Bill #{data['bill_no']}"):
            col_info, col_img = st.columns([1, 2])

            with col_info:
                st.write(f"**Bill No:** {data['bill_no']}")
                st.write(f"**Period:** {start_date} to {end_date}")
                st.write(f"**Usage:** {usage}")
                st.write(f"**Water:** ${water}")
                st.write(f"**Sewage:** ${sewage}")
                st.write(f"**Total Amount:** ${bill_amount}")

            with col_img:
                if "image" in data and data["image"]:
                    # Decode base64 image and display
                    image_data = base64.b64decode(data["image"])
                    st.image(
                        image_data,
                        caption=f"Bill Image - {uploaded_file.name}",
                        use_container_width=True,
                    )
                else:
                    st.info("No image available for this bill")


   
