from sqlalchemy import String, Date, Numeric, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[str] = mapped_column(Date, nullable=False)
    merchant: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)

Index("ix_transactions_date", Transaction.date)
Index("ix_transactions_category", Transaction.category)
Index("ix_transactions_merchant", Transaction.merchant)
