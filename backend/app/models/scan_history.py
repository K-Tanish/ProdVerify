from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship, validates

from backend.app.database import Base


class ScanHistory(Base):
    __tablename__ = "scan_history"

    scan_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(
        String(64),
        ForeignKey("products.product_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    scan_type = Column(String(50), nullable=False, index=True)
    scanned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    scan_location = Column(String(255), nullable=True)
    result = Column(String(50), nullable=False, index=True)
    risk_reason = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "scan_type IN ('EXTERNAL_VERIFICATION', 'INTERNAL_REGISTRATION')",
            name="chk_scan_type",
        ),
        CheckConstraint(
            "result IN ('VERIFIED', 'SUSPICIOUS', 'INVALID')",
            name="chk_scan_result",
        ),
    )

    # Relationships
    product = relationship("Product", back_populates="scans")

    @validates("scan_type")
    def validate_scan_type(self, key, value):
        allowed = {"EXTERNAL_VERIFICATION", "INTERNAL_REGISTRATION"}
        if value not in allowed:
            raise ValueError(f"scan_type must be one of {allowed}, got {value}")
        return value

    @validates("result")
    def validate_result(self, key, value):
        allowed = {"VERIFIED", "SUSPICIOUS", "INVALID"}
        if value not in allowed:
            raise ValueError(f"result must be one of {allowed}, got {value}")
        return value

    def __repr__(self):
        return (
            f"<ScanHistory id={self.scan_id} product_id='{self.product_id}' "
            f"type='{self.scan_type}' result='{self.result}'>"
        )
