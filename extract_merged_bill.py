from entities import Bill
from typing import Optional
import base64
from dotenv import load_dotenv
from mistralai import Mistral
from pydantic import BaseModel, Field
from mistralai.extra import response_format_from_pydantic_model
import os

load_dotenv()

api_key = os.environ["MISTRAL_API_KEY"]

client = Mistral(api_key=api_key)


def extract_single_bills(bill: bytes):
    encode_bill = base64.b64encode(bill).decode("utf-8")
    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        pages=list(range(4)),
        document={
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{encode_bill}",
        },
    )

    return ocr_response.document_annotation
