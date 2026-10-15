import re
from sqlalchemy import CheckConstraint, Column, Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship, validates

from backend.app.database import Base


class WarrantyRegistration(Base):
    __tablename__ = "warranty_registrations"

    registration_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(
        String(64),
        ForeignKey("products.product_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    customer_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    retailer_id = Column(
        Integer,
        ForeignKey("retailers.retailer_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    purchase_price = Column(Float, nullable=True)
    purchase_date = Column(Date, nullable=False)
    warranty_status = Column(String(50), nullable=False, default="ACTIVE")
    warranty_start_date = Column(Date, nullable=False)
    warranty_end_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "warranty_status IN ('ACTIVE', 'EXPIRED', 'VOID')",
            name="chk_warranty_status",
        ),
        CheckConstraint(
            "warranty_end_date >= warranty_start_date",
            name="chk_warranty_dates",
        ),
        CheckConstraint("length(trim(customer_name)) > 0", name="chk_customer_name_not_empty"),
        CheckConstraint("length(trim(email)) > 0", name="chk_warranty_email_not_empty"),
    )

    # Relationships
    product = relationship("Product", back_populates="warranty_registration")
    retailer = relationship("Retailer", back_populates="warranty_registrations")

    @validates("customer_name")
    def validate_name(self, key, value):
        if not value or not str(value).strip():
            raise ValueError("customer_name cannot be empty or whitespace.")
        return str(value).strip()

    @validates("email")
    def validate_email(self, key, value):
        if not value or not str(value).strip():
            raise ValueError("email cannot be empty or whitespace.")
        cleaned = str(value).strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", cleaned):
            raise ValueError(f"Invalid email address: {value}")
        return cleaned

    @validates("warranty_status")
    def validate_status(self, key, value):
        allowed = {"ACTIVE", "EXPIRED", "VOID"}
        if value not in allowed:
            raise ValueError(f"warranty_status must be one of {allowed}, got {value}")
        return value

    @validates("purchase_price")
    def validate_price(self, key, value):
        if value is not None and value < 0:
            raise ValueError("purchase_price cannot be negative.")
        return value

    def __repr__(self):
        return (
            f"<WarrantyRegistration id={self.registration_id} product_id='{self.product_id}' "
            f"status='{self.warranty_status}'>"
        )
