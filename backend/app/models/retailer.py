from sqlalchemy import CheckConstraint, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship, validates

from backend.app.database import Base


class Retailer(Base):
    __tablename__ = "retailers"

    retailer_id = Column(Integer, primary_key=True, autoincrement=True)
    retailer_name = Column(String(255), nullable=False, index=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("length(trim(retailer_name)) > 0", name="chk_retailer_name_not_empty"),
        CheckConstraint("length(trim(city)) > 0", name="chk_retailer_city_not_empty"),
        CheckConstraint("length(trim(state)) > 0", name="chk_retailer_state_not_empty"),
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="chk_retailer_status"),
    )

    # Relationships
    products = relationship("Product", back_populates="intended_retailer")
    warranty_registrations = relationship("WarrantyRegistration", back_populates="retailer")

    @validates("retailer_name")
    def validate_name(self, key, value):
        if not value or not str(value).strip():
            raise ValueError("retailer_name cannot be empty or whitespace.")
        return str(value).strip()

    @validates("city", "state")
    def validate_location(self, key, value):
        if not value or not str(value).strip():
            raise ValueError(f"{key} cannot be empty or whitespace.")
        return str(value).strip()

    @validates("status")
    def validate_status(self, key, value):
        allowed = {"ACTIVE", "INACTIVE"}
        if value not in allowed:
            raise ValueError(f"status must be one of {allowed}, got {value}")
        return value

    def __repr__(self):
        return f"<Retailer id={self.retailer_id} name='{self.retailer_name}' city='{self.city}' state='{self.state}'>"
