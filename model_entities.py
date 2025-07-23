from typing import Optional, List
from pydantic import BaseModel, Field


class Date(BaseModel):
    day: int = Field(
        ...,
        description="The number of day of the month of the date, can range from 1 to 31",
    )
    month: int = Field(
        ...,
        description="The number of month of the year of the date, can range from 1 to 12",
    )
    year: int = Field(..., description="The year of the date")


class Bill(BaseModel):
    page_no: int = Field(
        ..., description="The page number from which this infromation was extracted. "
    )
    previous_date: Date = Field(
        ..., description="The previous date of the bill reading e.g. 2022-06-30"
    )
    current_date: Date = Field(
        ..., description="The current date of the bill e.g. 03-01-2023  "
    )
    consumption: float = Field(
        ..., description="The total consumption of water in m3, e.g. 2268.89 "
    )
    total_bill: float = Field(
        ..., description="The total current bill of water, e.g. $10,475.69 "
    )
    sewage: Optional[float] = Field(None, description="The sewage amount if available")
    bill_no: str = Field(..., description="The serial number of the bill")


class Bills(BaseModel):
    bills: List[Bill] = Field(..., description="The list of bills")
