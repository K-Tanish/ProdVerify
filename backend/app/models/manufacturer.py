import re
from sqlalchemy import CheckConstraint, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship, validates

from backend.app.database import Base


class Manufacturer(Base):
    __tablename__ = "manufacturers"

    manufacturer_id = Column(Integer, primary_key=True, autoincrement=True)
    manufacturer_name = Column(String(255), nullable=False, unique=True, index=True)
    contact_email = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("length(trim(manufacturer_name)) > 0", name="chk_manufacturer_name_not_empty"),
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')", name="chk_manufacturer_status"),
    )

    # Relationships
    products = relationship("Product", back_populates="manufacturer", cascade="all, delete-orphan")

    @validates("manufacturer_name")
    def validate_name(self, key, value):
        if not value or not str(value).strip():
            raise ValueError("manufacturer_name cannot be empty or whitespace.")
        return str(value).strip()

    @validates("contact_email")
    def validate_email(self, key, value):
        if value is not None:
            cleaned = str(value).strip()
            if cleaned and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", cleaned):
                raise ValueError(f"Invalid email address: {value}")
            return cleaned
        return value

    @validates("status")
    def validate_status(self, key, value):
        allowed = {"ACTIVE", "INACTIVE", "SUSPENDED"}
        if value not in allowed:
            raise ValueError(f"status must be one of {allowed}, got {value}")
        return value

    def __repr__(self):
        return f"<Manufacturer id={self.manufacturer_id} name='{self.manufacturer_name}'>"
