from httpx.__version__ import __description__
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


class Bill(BaseModel):
    previous_date: str = Field(
        ..., description="The previous date of the bill reading e.g. 2022-06-30"
    )
    current_date: str = Field(
        ..., description="The current date of the bill e.g. 03-01-2023  "
    )
    consumption: float = Field(
        ..., description="The total consumption of water in m3, e.g. 2268.89 "
    )
    total_bill: float = Field(
        ..., description="The total current bill of water, e.g. $10,475.69 "
    )
    sewage: Optional[float] = Field(
        None, description="The sewage amount if available"
    )


def extract_data(bill: bytes):
    encode_bill = base64.b64encode(bill).decode("utf-8")
    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        pages=list(range(2)),
        document={
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{encode_bill}",
        },
        document_annotation_format=response_format_from_pydantic_model(Bill),
    )

    return str(ocr_response.document_annotation)
