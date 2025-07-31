from typing import Tuple
from api_entites import BillData, DateInfo
from model_entities import Bill, Date
from typing import Literal, Optional, List
from pydantic import BaseModel, Field
from typing import Annotated
import base64
from mistralai import Mistral
import os
from typing_extensions import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from google import genai
from google.genai import types
import json
import fitz  # PyMuPDF - pip install PyMuPDF
from PIL import Image
import io
import base64






class Bills(BaseModel):
    bills: List[Bill]


load_dotenv()

api_key = os.environ["MISTRAL_API_KEY"]

mistral_client = Mistral(api_key=api_key)
google_client = genai.Client()


class State(TypedDict):
    pdf: bytes
    content: str
    is_multiple_bills: bool
    bills: List[Bill]
    address: Optional[str]
    page_images: dict[int, str]


class Answer(BaseModel):
    address: str = Field(description="The address of the bill")
    is_multiple_bills: bool = Field(
        False,
        description="True if multiple billing periods/due dates are detected, False if single billing period",
    )


graph_builder = StateGraph(State)


def extract_content(state: State):
    encode_bill = base64.b64encode(state["pdf"]).decode("utf-8")
    ocr_response = mistral_client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{encode_bill}",
        },
    )

    # content = "".join(
    #     [
    #         f"\n\nPAGE NUMBER :{page.index}\n{page.markdown}"
    #         for page in ocr_response.pages
    #     ]
    # )

    content = ""

    for page in ocr_response.pages:
        content += f"\n\nPAGE NUMBER :{page.index}\n{page.markdown}"


        for image in page.images:

            if image.id and image.image_annotation:
                content.replace(image.id,image.image_annotation)

    return {**state, "content": content}


def check_multiple_bills(state: State):
    response = google_client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=types.Part.from_text(text=f"""
        The following information should be present together, only then you can extract them:
        1. Please look for current reading date.
        2. Please look for previous reading date.
        3. Please look for sewage cost. 
        4. Please look for water cost.
        5. Please for total bill. 
        The cost of water plus sewage should be equal to the total bill.
        water + sewage = total bill
        If you find this information together on a certain page, then you must also extract that certain page number.
        YOUR LIFE DEPENDS ON THIS!
        {state["content"]}"""),
        config=types.GenerateContentConfig(
            system_instruction="""Analyze this water bill content for multiple billing periods. 
                                    Key indicators of multiple bills:
                                    - Multiple due dates
                                    - Different billing start dates  
                                    - Different billing end dates
                                    - Different billing months/periods
                                    - Multiple meter reading dates

                                    Return true if multiple billing periods detected, false if single billing period. and return address of the bill""",
            temperature=0,
            top_p=0.95,
            top_k=20,
            candidate_count=1,
            seed=5,
            stop_sequences=["STOP!"],
            presence_penalty=0.0,
            frequency_penalty=0.0,
            response_mime_type="application/json",
            response_schema=Answer,
        ),
    )

    response_data = json.loads(response.text or "")

    return {
        **state,
        "is_multiple_bills": bool(response_data["is_multiple_bills"]),
        "address": response_data["address"],
    }


def is_multiple_bills(state: State) -> Literal["single_bill", "multiple_bills"]:
    return "multiple_bills" if state["is_multiple_bills"] else "single_bill"


def single_bill(state: State):

    response = google_client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=types.Part.from_text(text=state["content"]),
        config=types.GenerateContentConfig(
            system_instruction="You are an expert information extractor. Your job is to extract bill information given the provided schema",
            temperature=0,
            top_p=0.95,
            top_k=20,
            candidate_count=1,
            seed=5,
            stop_sequences=["STOP!"],
            presence_penalty=0.0,
            frequency_penalty=0.0,
            response_mime_type="application/json",
            response_schema=Bill,
        ),
    )

    bill_data = json.loads(response.text or "")
    bill = Bill(**bill_data)

    return {**state, "bills": [bill]}


def multiple_bills(state: State):

    response = google_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=types.Part.from_text(text=state["content"]),
        config=types.GenerateContentConfig(
            system_instruction="You are an expert information extractor. Your job is to extract bill information given the provided schema",
            temperature=0,
            top_p=0.95,
            top_k=20,
            candidate_count=1,
            seed=5,
            stop_sequences=["STOP!"],
            presence_penalty=0.0,
            frequency_penalty=0.0,
            response_mime_type="application/json",
            response_schema=Bills,
        ),
    )

    bills_data = json.loads(response.text or "")
    bills = []
    
    for bill_data in bills_data["bills"]:
        # Handle missing or invalid fields manually
        bill = Bill(
            page_no=bill_data["page_no"],
            previous_date=Date(
            day=bill_data["previous_date"]["day"],
            month=bill_data["previous_date"]["month"],
            year=bill_data["previous_date"]["year"]
            ),
            current_date=Date(
            day=bill_data["current_date"]["day"],
            month=bill_data["current_date"]["month"],
            year=bill_data["current_date"]["year"]
            ),
            consumption=bill_data["consumption"],
            total_bill=bill_data["total_bill"],
            sewage=bill_data["sewage"],
            bill_no=bill_data["bill_no"]
        )
        bills.append(bill)

    return {**state, "bills": bills}


def extract_images(state: State):

    # Open PDF from bytes (not base64 string)
    pdf_document = fitz.open(stream=state["pdf"], filetype="pdf")

    images = {}  # Dictionary to store page_number: image_data
    page_nos = [bill.page_no for bill in state["bills"]]

    for page_num in page_nos:

        if page_num < len(pdf_document):
            page = pdf_document[page_num]

            # Convert page to image (PNG)
            pix = page.get_pixmap(
                matrix=fitz.Matrix(2, 2)
            )  # 2x zoom for better quality
            img_data = pix.tobytes("png")

            # Convert to PIL Image for easier handling
            pil_image = Image.open(io.BytesIO(img_data))

            # Store as base64 for easy transmission
            buffered = io.BytesIO()
            pil_image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            images[page_num] = img_base64

    pdf_document.close()

    return {**state, "page_images": images}


graph_builder.add_node("extract_content", extract_content)
graph_builder.add_node("check_multiple_bills", check_multiple_bills)
graph_builder.add_node("multiple_bills", multiple_bills)
graph_builder.add_node("single_bill", single_bill)
graph_builder.add_node("extract_images", extract_images)

graph_builder.add_edge(START, "extract_content")
graph_builder.add_edge("extract_content", "check_multiple_bills")

graph_builder.add_conditional_edges("check_multiple_bills", is_multiple_bills)

graph_builder.add_edge("single_bill", "extract_images")
graph_builder.add_edge("multiple_bills", "extract_images")

graph_builder.add_edge("extract_images", END)

graph = graph_builder.compile()


def process_bill_pdf(pdf_bytes: bytes, filename: str) -> Tuple[str, List[BillData]]:
    """Process a PDF bill and return the final state with extracted data and images"""

    # Initial state
    initial_state = {
        "pdf": pdf_bytes,
        "content": "",
        "is_multiple_bills": False,
        "bills": [],
        "address": None,
        "page_images": {},
    }

    # Run the workflow
    final_state = graph.invoke(
        initial_state
    )  # Transform workflow results to API format
    bill_data_list: list[BillData] = []

    for bill in final_state["bills"]:
        # Get the page image for this bill
        page_image = final_state["page_images"][bill.page_no]

        bill_data = BillData(
            file_name=filename,
            bill_no=bill.bill_no,
            start_date=DateInfo(
                day=bill.previous_date.day,
                month=bill.previous_date.month,
                year=bill.previous_date.year,
            ),
            end_date=DateInfo(
                day=bill.current_date.day,
                month=bill.current_date.month,
                year=bill.current_date.year,
            ),
            usage=bill.consumption,
            water=bill.total_bill,
            sewage=bill.sewage,
            bill_amount=bill.total_bill + (bill.sewage or 0),
            image=page_image,
        )

        bill_data_list.append(bill_data)

    # Return in API format
    return (
        final_state.get("address", "Address not found"),
        bill_data_list,
    )
