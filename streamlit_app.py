import streamlit as st
import pandas as pd
import json
from extraction import extract_data
from typing import List
import io

st.set_page_config(page_title="Bill Parser", page_icon="📄", layout="wide")

st.title("📄 Water Bill Data Extractor")
st.markdown("Upload your water bill PDFs to extract key information automatically.")

# File uploader
uploaded_files = st.file_uploader(
    "Choose PDF files",
    type="pdf",
    accept_multiple_files=True,
    help="Upload one or more PDF water bills to extract data",
)

if uploaded_files:
    st.markdown(f"**{len(uploaded_files)} files uploaded**")

    # Process button
    if st.button("🔍 Extract Data", type="primary"):
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        results = []

        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")

            try:
                # Read file content
                file_content = uploaded_file.read()

                # Validate PDF
                if not file_content.startswith(b"%PDF"):
                    st.error(f"❌ {uploaded_file.name} is not a valid PDF file")
                    continue

                # Extract data
                extracted_data = extract_data(file_content)

                # Parse the JSON response
                if isinstance(extracted_data, str):
                    data = json.loads(extracted_data)
                else:
                    data = (
                        json.loads(extracted_data)
                        if hasattr(extracted_data, "model_dump_json")
                        else extracted_data
                    )

                # Add filename to results
                result = {
                    "filename": uploaded_file.name,
                    "previous_date": f"{data['previous_date']['day']:02d}-{data['previous_date']['month']:02d}-{data['previous_date']['year']}",
                    "current_date": f"{data['current_date']['day']:02d}-{data['current_date']['month']:02d}-{data['current_date']['year']}",
                    "consumption": data["consumption"],
                    "total_bill": data.get("total_bill", data.get("current_bill", 0)),
                    "sewage": data.get("sewage", "N/A"),
                }

                results.append(result)

            except Exception as e:
                st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")

            # Update progress
            progress_bar.progress((i + 1) / len(uploaded_files))

        # Clear status text
        status_text.empty()
        progress_bar.empty()

        if results:
            st.success(f"✅ Successfully processed {len(results)} files!")

            # Create DataFrame
            df = pd.DataFrame(results)

            # Display results in a nice table
            st.markdown("## 📊 Extracted Data")

            # Format the dataframe for better display
            df_display = df.copy()
            df_display["consumption"] = df_display["consumption"].apply(
                lambda x: f"{x:.2f} m³"
            )
            df_display["total_bill"] = df_display["total_bill"].apply(
                lambda x: f"${x:,.2f}"
            )

            # Rename columns for better display
            df_display.columns = [
                "File Name",
                "Previous Date",
                "Current Date",
                "Consumption",
                "Total Bill",
                "Sewage",
            ]

            # Display the table
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # Summary statistics
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Files Processed", len(results))

            with col2:
                total_consumption = df["consumption"].sum()
                st.metric("Total Consumption", f"{total_consumption:.2f} m³")

            with col3:
                total_amount = df["total_bill"].sum()
                st.metric("Total Amount", f"${total_amount:,.2f}")

            # Download option
            st.markdown("## 💾 Download Results")

            # Convert to CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name="water_bills_extracted_data.csv",
                mime="text/csv",
            )

            # Convert to JSON
            json_data = df.to_json(orient="records", indent=2)

            st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name="water_bills_extracted_data.json",
                mime="application/json",
            )

        else:
            st.warning("⚠️ No files were successfully processed.")

else:
    # Instructions when no files are uploaded
    st.info(
        """
    👆 **Instructions:**
    1. Upload one or more PDF water bills using the file uploader above
    2. Click the "Extract Data" button to process the files
    3. View the extracted data in a table format
    4. Download the results as CSV or JSON
    
    **Extracted Information:**
    - Previous reading date
    - Current reading date  
    - Water consumption (m³)
    - Total bill amount
    - Sewage charges (if available)
    """
    )

# Sidebar with additional info
with st.sidebar:
    st.markdown("## ℹ️ About")
    st.markdown(
        """
    This application uses AI-powered OCR to extract key information from water bill PDFs.
    
    **Supported formats:**
    - PDF files only
    - Multiple files at once
    
    **Extracted data:**
    - Billing period dates
    - Water consumption
    - Bill amounts
    - Sewage charges
    """
    )

    st.markdown("## 🔧 Technical Details")
    st.markdown(
        """
    - **OCR Engine:** Mistral OCR
    - **Data Format:** Structured JSON
    - **Export Options:** CSV, JSON
    """
    )
