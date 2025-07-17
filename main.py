from importlib.resources._functional import contents
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from extraction import extract_data

app = FastAPI()


@app.post("/extract-bills")
async def extract_batch(bills: List[UploadFile] = File(...)):
    results = []

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

        results.append(extract_data(content))

  
    return {"results": results}
