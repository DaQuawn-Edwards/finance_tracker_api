from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

import pandas as pd
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import Transaction
from .schemas import TransactionOut, UploadResult

# Starter approach: create tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Finance Tracker API (CSV Ingestion)",
    version="0.1.0",
    description="Upload CSV transactions, store them in PostgreSQL, and query them. Swagger UI at /docs.",
)

REQUIRED_COLUMNS = ["date", "merchant", "amount", "category"]

@app.get("/health")
def health():
    return {"status": "ok"}

def _normalize_merchant(s: str) -> str:
    return " ".join(s.strip().split())

def _parse_date(value: object, row_idx: int) -> date:
    try:
        return pd.to_datetime(value).date()
    except Exception:
        raise ValueError(f"Row {row_idx}: invalid date '{value}' (expected YYYY-MM-DD)")

def _parse_amount(value: object, row_idx: int) -> Decimal:
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        raise ValueError(f"Row {row_idx}: invalid amount '{value}'")

@app.post("/upload-csv", response_model=UploadResult)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        df = pd.read_csv(pd.io.common.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {missing}")

    inserted = 0
    skipped = 0
    errors: list[str] = []

    seen: set[tuple[str, str, str, str]] = set()

    for i, row in df.iterrows():
        row_idx = i + 2
        try:
            d = _parse_date(row["date"], row_idx)
            merchant = _normalize_merchant(str(row["merchant"]))
            category = str(row["category"]).strip()
            amount = _parse_amount(row["amount"], row_idx)

            if not merchant or not category:
                raise ValueError(f"Row {row_idx}: merchant/category cannot be blank")

            key = (str(d), merchant.lower(), str(amount), category.lower())
            if key in seen:
                skipped += 1
                continue
            seen.add(key)

            db.add(Transaction(date=d, merchant=merchant, amount=amount, category=category))
            inserted += 1
        except Exception as e:
            errors.append(str(e))

    if inserted == 0 and errors:
        db.rollback()
        return UploadResult(inserted=0, skipped=skipped, errors=errors)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database insert failed: {e}")

    return UploadResult(inserted=inserted, skipped=skipped, errors=errors)

@app.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
    category: Optional[str] = Query(None),
    merchant: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort: str = Query("date_desc", description="date_desc|date_asc|amount_desc|amount_asc"),
    db: Session = Depends(get_db),
):
    q = select(Transaction)

    if start:
        q = q.where(Transaction.date >= start)
    if end:
        q = q.where(Transaction.date <= end)
    if category:
        q = q.where(Transaction.category == category)
    if merchant:
        q = q.where(Transaction.merchant.ilike(f"%{merchant}%"))

    if sort == "date_desc":
        q = q.order_by(Transaction.date.desc(), Transaction.id.desc())
    elif sort == "date_asc":
        q = q.order_by(Transaction.date.asc(), Transaction.id.asc())
    elif sort == "amount_desc":
        q = q.order_by(Transaction.amount.desc(), Transaction.id.desc())
    elif sort == "amount_asc":
        q = q.order_by(Transaction.amount.asc(), Transaction.id.asc())
    else:
        raise HTTPException(status_code=400, detail="Invalid sort option")

    q = q.limit(limit).offset(offset)
    return db.execute(q).scalars().all()
