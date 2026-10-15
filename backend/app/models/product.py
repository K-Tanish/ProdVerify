from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship, validates

from backend.app.database import Base


class Product(Base):
    __tablename__ = "products"

    product_id = Column(String(64), primary_key=True)
    product_name = Column(String(255), nullable=False)
    manufacturer_id = Column(
        Integer,
        ForeignKey("manufacturers.manufacturer_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    serial_number = Column(String(100), unique=True, nullable=False, index=True)
    external_qr_token = Column(String(128), unique=True, nullable=False, index=True)
    internal_qr_token = Column(String(128), unique=True, nullable=False, index=True)
    manufacturing_location = Column(String(255), nullable=True)
    intended_retailer_id = Column(
        Integer,
        ForeignKey("retailers.retailer_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    product_status = Column(String(50), nullable=False, default="IN_STOCK")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("external_qr_token != internal_qr_token", name="chk_tokens_differ"),
        CheckConstraint("product_status IN ('IN_STOCK', 'SOLD', 'BLOCKED')", name="chk_product_status"),
        CheckConstraint("length(trim(product_id)) > 0", name="chk_product_id_not_empty"),
        CheckConstraint("length(trim(product_name)) > 0", name="chk_product_name_not_empty"),
        CheckConstraint("length(trim(serial_number)) > 0", name="chk_product_serial_not_empty"),
        CheckConstraint("length(trim(external_qr_token)) > 0", name="chk_product_ext_token_not_empty"),
        CheckConstraint("length(trim(internal_qr_token)) > 0", name="chk_product_int_token_not_empty"),
    )

    # Relationships
    manufacturer = relationship("Manufacturer", back_populates="products")
    intended_retailer = relationship("Retailer", back_populates="products")
    scans = relationship("ScanHistory", back_populates="product", cascade="all, delete-orphan")
    warranty_registration = relationship(
        "WarrantyRegistration",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )

    @validates("product_id", "product_name", "serial_number")
    def validate_non_empty(self, key, value):
        if not value or not str(value).strip():
            raise ValueError(f"{key} cannot be empty or whitespace.")
        return str(value).strip()

    @validates("external_qr_token")
    def validate_external_token(self, key, value):
        if not value or not str(value).strip():
            raise ValueError("external_qr_token cannot be empty or whitespace.")
        cleaned = str(value).strip()
        if self.internal_qr_token and cleaned == self.internal_qr_token:
            raise ValueError("external_qr_token must differ from internal_qr_token.")
        return cleaned

    @validates("internal_qr_token")
    def validate_internal_token(self, key, value):
        if not value or not str(value).strip():
            raise ValueError("internal_qr_token cannot be empty or whitespace.")
        cleaned = str(value).strip()
        if self.external_qr_token and cleaned == self.external_qr_token:
            raise ValueError("internal_qr_token must differ from external_qr_token.")
        return cleaned

    @validates("product_status")
    def validate_status(self, key, value):
        allowed = {"IN_STOCK", "SOLD", "BLOCKED"}
        if value not in allowed:
            raise ValueError(f"product_status must be one of {allowed}, got {value}")
        return value

    def __repr__(self):
        return (
            f"<Product id='{self.product_id}' name='{self.product_name}' "
            f"serial='{self.serial_number}' status='{self.product_status}'>"
        )
