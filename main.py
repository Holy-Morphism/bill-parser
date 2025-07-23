from workflow import process_bill_pdf
from api_entites import (
    ExtractResponse,
    RootResponse,
    DateInfo,
    BillData,
)
from typing_extensions import Literal
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
import os


app = FastAPI(
    title="Bill Parser API",
    description="""
    Water Bill Data Extraction API
    
    This API uses Mistral OCR + Gemini API to extract structured data from water bill PDFs.
    
    Features:
    - Multi-file processing: Upload multiple PDF files simultaneously
    - Parallel processing: Efficient concurrent extraction for faster results
    - Data validation: Comprehensive PDF format validation and error handling
    - Flexible output: Choose between individual or merged result formats
    
    Supported Data Fields:
    - Bill number and account information
    - Previous and current meter reading dates
    - Water consumption in cubic meters
    - Total bill amount and sewage charges
    - Customer address information
    
    Usage:
    1. Upload one or more PDF water bills
    2. Choose processing mode (single or merged)
    3. Receive structured JSON data with extracted information
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Bill Parser API Support",
        "email": "support@billparser.com",
    },
    tags_metadata=[
        {
            "name": "extraction",
            "description": "PDF bill data extraction endpoints",
        },
        {
            "name": "health",
            "description": "API health and status monitoring",
        },
        {
            "name": "info",
            "description": "General API information",
        },
    ],
)


@app.get("/", response_model=RootResponse, tags=["info"])
async def root():
    """
    Returns basic information about the API including:
    - Service status
    - Available endpoints

    Returns:
        RootResponse: API information and available endpoints

    Example Response:
        ```json
        {
            "message": "Welcome to Bill Parser API",
            "status": "running",
            "endpoints": {
                "extract_bills": "/extract-bills",
                "docs": "/docs",
            }
        }
        ```
    """
    return {
        "message": "Welcome to Bill Parser API",
        "status": "running",
        "endpoints": {
            "extract_bills": "/extract-bills",
            "docs": "/docs",
        },
    }


@app.post("/extract-bills", response_model=ExtractResponse, tags=["extraction"])
async def extract_batch(
    bills: List[UploadFile] = File(
        ...,
        description="One or more PDF files containing water bills",
        example="[water_bill_01.pdf, water_bill_02.pdf]",
    ),
    mode: Optional[Literal["merged", "single"]] = Query(
        None,
        description="Processing mode: 'single' for individual extraction, 'merged' for combined results",
        example="single",
    ),
):
    """
    Extract structured data from water bill PDFs
    
    This endpoint processes uploaded PDF files and extracts key information such as:
    - Bill number and account information
    - Previous and current meter reading dates  
    - Water consumption amount in cubic meters
    - Total bill amount and sewage charges
    - Customer address information
    
    **Processing Modes:**
    - `single` (default): Process each bill individually and return separate results
    - `merged`: Combine all bill data into a single aggregated result
    
    **Supported File Types:**
    - PDF files only (validated by content type and file headers)
    - Files must contain readable text content
    
    **Performance:**
    - Files processed concurrently for optimal speed
    - Maximum concurrent workers equal to number of files
    - Automatic PDF validation and error handling
    
    Args:
        bills: List of PDF files to process (required)
        mode: Processing mode - 'single' or 'merged' (optional, defaults to individual processing)
    
    Returns:
        ExtractResponse: Structured data including customer address and bill details
    
    Raises:
        HTTPException 400: Invalid file type, corrupted PDF, or validation failure
        HTTPException 500: Internal processing error during extraction
    
    Example Usage:
        ```bash
        # Upload single file
        curl -X POST "http://localhost:8000/extract-bills" \\
             -H "Content-Type: multipart/form-data" \\
             -F "bills=@water_bill.pdf"
             
        # Upload multiple files with mode
        curl -X POST "http://localhost:8000/extract-bills?mode=single" \\
             -H "Content-Type: multipart/form-data" \\
             -F "bills=@water_bill_1.pdf" \\
             -F "bills=@water_bill_2.pdf"
        ```
        
    Example Response:
        ```json
        {
            "address": "123 Main Street, City, State 12345",
            "bills": [
                {
                    "file_name": "water_bill_1.pdf",
                    "bill_no": "WB123456",
                    "start_date": {"day": 1, "month": 1, "year": 2024},
                    "end_date": {"day": 31, "month": 1, "year": 2024},
                    "usage": 15.5,
                    "water": 45.20,
                    "sewage": 12.30,
                    "bill_amount": 57.50
                }
            ]
        }
        ```
    """
    all_bills = []
    address = None

    for bill in bills:
        # Check if file is a PDF
        if bill.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"File '{bill.filename}' is not a PDF. Received: {bill.content_type}",
            )

        # Read and validate PDF magic number (most reliable)
        content = await bill.read()
        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=400,
                detail=f"File '{bill.filename}' is not a valid PDF file",
            )

        # Reset file pointer for further processing
        await bill.seek(0)

        content = await bill.read()

        address, result = process_bill_pdf(content, bill.filename)
            
        # Add bills to the list
        all_bills.extend(result)

            

    return ExtractResponse(
        address=address or "Address not found",
        bills=all_bills
    )
