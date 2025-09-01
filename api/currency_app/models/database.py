"""SQLAlchemy database models."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, Numeric, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ConversionHistory(Base):
    """Database model for conversion history."""

    __tablename__ = "conversion_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversion_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    request_id = Column(String(36), nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    from_currency = Column(String(3), nullable=False)
    to_currency = Column(String(3), nullable=False)
    converted_amount = Column(Numeric(15, 2), nullable=False)
    exchange_rate = Column(Numeric(10, 6), nullable=False)
    conversion_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        """Return string representation of ConversionHistory."""
        return (
            f"<ConversionHistory("
            f"id={self.id}, "
            f"conversion_id='{self.conversion_id}', "
            f"from_currency='{self.from_currency}', "
            f"to_currency='{self.to_currency}', "
            f"amount={self.amount}"
            f")>"
        )
