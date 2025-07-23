from pydantic import BaseModel, Field
from typing import List, Optional


# Response models for API documentation
class DateInfo(BaseModel):
    """Date information with day, month, and year"""

    day: int = Field(..., description="Day of the month (1-31)")
    month: int = Field(..., description="Month of the year (1-12)")
    year: int = Field(..., description="Year (e.g., 2024)")

    class Config:
        json_schema_extra = {"example": {"day": 15, "month": 3, "year": 2024}}


class BillData(BaseModel):
    """Bill data extracted from PDF"""

    file_name: str = Field(..., description="Original filename of the processed PDF")
    bill_no: str = Field(..., description="Bill or account number")
    start_date: DateInfo = Field(..., description="Previous meter reading date")
    end_date: DateInfo = Field(..., description="Current meter reading date")
    usage: float = Field(..., description="Water consumption in cubic meters")
    water: float = Field(..., description="Water charges amount")
    sewage: Optional[float] = Field(None, description="Sewage charges (if applicable)")
    bill_amount: float = Field(..., description="Total bill amount")
    image: Optional[str] = Field(None, description="Bill image in base64 format")

    class Config:
        json_schema_extra = {
            "example": {
                "file_name": "water_bill_march_2024.pdf",
                "bill_no": "WB123456789",
                "start_date": {"day": 1, "month": 3, "year": 2024},
                "end_date": {"day": 31, "month": 3, "year": 2024},
                "usage": 15.5,
                "water": 45.20,
                "sewage": 12.30,
                "bill_amount": 57.50,
                "image":"..."
            }
        }


class ExtractResponse(BaseModel):
    """Response model for bill extraction"""

    address: str = Field(..., description="Customer address extracted from the bill")
    bills: List[BillData] = Field(..., description="List of extracted bill data")

    class Config:
        json_schema_extra = {
            "example": {
                "address": "123 Main Street, Anytown, ST 12345",
                "bills": [
                    {
                        "file_name": "water_bill_march_2024.pdf",
                        "bill_no": "WB123456789",
                        "start_date": {"day": 1, "month": 3, "year": 2024},
                        "end_date": {"day": 31, "month": 3, "year": 2024},
                        "usage": 15.5,
                        "water": 45.20,
                        "sewage": 12.30,
                        "bill_amount": 57.50,
                    }
                ],
            }
        }


class RootResponse(BaseModel):
    """Root endpoint response"""

    message: str = Field(..., description="Welcome message")
    endpoints: dict = Field(..., description="Available API endpoints")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Welcome to Bill Parser API",
                "status": "running",
                "endpoints": {
                    "extract_bills": "/extract-bills",
                    "docs": "/docs",
                },
            }
        }
