from typing_extensions import Literal
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException
import concurrent.futures
from extract_single_bill import extract_single_bills

app = FastAPI()


@app.get("/")
async def root():
    return {
        "message": "Welcome to Bill Parser API",
        "status": "running",
        "endpoints": {
            "extract_bills": "/extract-bills",
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.post("/extract-bills")
async def extract_batch(
    bills: List[UploadFile] = File(...),
    mode: Optional[Literal["merged", "single"]] = None,
):
    results = []
    contents = []

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

        contents.append(content)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(extract_single_bills, content) for content in contents]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()  # this gets the return value of the worker
            results.append(result)
    
    

    return {"results": results}
