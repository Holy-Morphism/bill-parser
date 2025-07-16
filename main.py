from typing import List
from fastapi import FastAPI, UploadFile, File


app = FastAPI()



@app.post("/extract-bills")
async def extract_batch(bills: List[UploadFile] = File(...)):
    results = []