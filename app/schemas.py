from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

class TransactionOut(BaseModel):
    id: int
    date: date
    merchant: str
    amount: Decimal
    category: str

    class Config:
        from_attributes = True

class UploadResult(BaseModel):
    inserted: int = Field(..., ge=0)
    skipped: int = Field(..., ge=0)
    errors: list[str] = []
