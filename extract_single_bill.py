from model_entities import Bill, BillAddresss
import base64
from dotenv import load_dotenv
from mistralai import Mistral
import os
from google import genai
from google.genai import types
import json
from api_entites import BillData, DateInfo

load_dotenv()

api_key = os.environ["MISTRAL_API_KEY"]

mistral_client = Mistral(api_key=api_key)
google_client = genai.Client()


def extract_single_bill(file_name: str, bill: bytes):
    encode_bill = base64.b64encode(bill).decode("utf-8")
    ocr_response = mistral_client.ocr.process(
        model="mistral-ocr-latest",
        pages=list(range(4)),
        document={
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{encode_bill}",
        },
    )

    content = "".join([page.markdown for page in ocr_response.pages])

    response = google_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=types.Part.from_text(text=content),
        config=types.GenerateContentConfig(
            system_instruction="You are an expert information extractor. Your job is to extract bill information given the provided schema",
            temperature=0,
            top_p=0.95,
            top_k=20,
            candidate_count=1,
            seed=5,
            max_output_tokens=65536,
            stop_sequences=["STOP!"],
            presence_penalty=0.0,
            frequency_penalty=0.0,
            response_mime_type="application/json",
            response_schema=Bill,
        ),
    )

    response_data = json.loads(response.text)
    # previous_date = json.loads(response_data["previous_date"])
    # current_date = json.loads(response_data["current_date"])

    # start_date = DateInfo(
    #     day=int(previous_date["day"]),
    #     month=int(previous_date["month"]),
    #     year=int(previous_date["year"]),
    # )
    # end_date = DateInfo(
    #     day=int(current_date["day"]),
    #     month=int(current_date["month"]),
    #     year=int(current_date["year"]),
    # )
    sewage_no =  response_data["sewage"] if response_data["sewage"] else 0

    # Create and return BillData object
    return BillData(
        file_name=file_name,
        bill_no=response_data["bill_no"],
        start_date=response_data["previous_date"],
        end_date=response_data["current_date"],
        usage=response_data["consumption"],
        water=response_data["total_bill"],
        sewage=response_data["sewage"],
        bill_amount=float(response_data["total_bill"]) + float(sewage_no),  # Adjust mapping as needed
    )


def extract_address(bill: bytes) -> str:
    encode_bill = base64.b64encode(bill).decode("utf-8")
    ocr_response = mistral_client.ocr.process(
        model="mistral-ocr-latest",
        pages=list(range(4)),
        document={
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{encode_bill}",
        },
    )

    content = "".join([page.markdown for page in ocr_response.pages])

    response = google_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=types.Part.from_text(text=content),
        config=types.GenerateContentConfig(
            system_instruction="You are an expert information extractor. Your job is to extract bill information given the provided schema",
            temperature=0,
            top_p=0.95,
            top_k=20,
            candidate_count=1,
            seed=5,
            max_output_tokens=10000,
            stop_sequences=["STOP!"],
            presence_penalty=0.0,
            frequency_penalty=0.0,
            response_mime_type="application/json",
            response_schema=BillAddresss,
        ),
    )

    return str(json.loads(response.text)["address"])
