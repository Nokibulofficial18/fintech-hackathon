from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin


class StudentProfile(Base, TimestampMixin):
    """Database model for international student financial profile."""

    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    home_country: Mapped[str] = mapped_column(String(60), nullable=False)
    destination_country: Mapped[str] = mapped_column(String(60), nullable=False)
    
    # Explicit ISO-4217 Currency Codes (e.g., INR, USD, GBP, CAD, EUR)
    home_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    destination_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    
    university_name: Mapped[str] = mapped_column(String(150), nullable=False)
    program_name: Mapped[str] = mapped_column(String(100), nullable=False)
    intake_term: Mapped[str] = mapped_column(String(30), nullable=False, default="Fall 2026")
