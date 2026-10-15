from pathlib import Path
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.app.config import BASE_VERIFY_URL, QR_STORAGE_DIR
from backend.app.database import get_db
from backend.app.models.product import Product
from backend.app.models.retailer import Retailer
from backend.app.services.qr_service import (
    build_registration_url,
    build_verification_url,
    generate_product_qr_files,
)
from backend.app.services.verification_service import verify_external_token

app = FastAPI(
    title="ProdVerify API",
    description="Counterfeit-product detection and warranty-tracking API",
    version="1.0.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Jinja2 templates directory
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ---------------------------------------------------------
# Health Endpoints
# ---------------------------------------------------------
@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"])
def health_check():
    return {"status": "healthy", "service": "ProdVerify API"}


# ---------------------------------------------------------
# Customer Verification Endpoints
# ---------------------------------------------------------
@app.get("/api/verify/{token}", tags=["Verification"])
def api_verify_product(
    token: str,
    reported_retailer_id: Optional[int] = Query(None, description="Customer-selected retailer ID"),
    scan_location: Optional[str] = Query(None, description="Optional scan location/city"),
    db: Session = Depends(get_db),
):
    """
    Perform external pre-purchase product verification.
    Resolves the external token strictly through the database.
    Logs scan attempt in Scan_History and returns VERIFIED, SUSPICIOUS, or INVALID.
    """
    return verify_external_token(
        session=db,
        token=token,
        reported_retailer_id=reported_retailer_id,
        scan_location=scan_location,
    )


@app.get("/verify/{token}", response_class=HTMLResponse, tags=["Web UI"])
def view_verification_page(request: Request, token: str):
    """Render the customer-facing external verification page."""
    return templates.TemplateResponse(
        request,
        "verify.html",
        {"token": token},
    )



# ---------------------------------------------------------
# Retailers & Products Endpoints
# ---------------------------------------------------------
@app.get("/api/retailers", tags=["Retailers"])
def list_retailers(db: Session = Depends(get_db)):
    """List all available retailers for location verification."""
    retailers = db.query(Retailer).filter_by(status="ACTIVE").all()
    return [
        {
            "retailer_id": r.retailer_id,
            "retailer_name": r.retailer_name,
            "address": r.address,
            "city": r.city,
            "state": r.state,
            "status": r.status,
        }
        for r in retailers
    ]


@app.get("/api/products", tags=["Products"])
def list_products(db: Session = Depends(get_db)):
    """List all products in the system."""
    products = db.query(Product).order_by(Product.product_id).all()
    return [
        {
            "product_id": p.product_id,
            "product_name": p.product_name,
            "serial_number": p.serial_number,
            "product_status": p.product_status,
            "manufacturing_location": p.manufacturing_location,
            "intended_retailer": {
                "retailer_id": p.intended_retailer.retailer_id,
                "retailer_name": p.intended_retailer.retailer_name,
                "city": p.intended_retailer.city,
                "state": p.intended_retailer.state,
            }
            if p.intended_retailer
            else None,
        }
        for p in products
    ]


@app.get("/api/products/{product_id}", tags=["Products"])
def get_product(product_id: str, db: Session = Depends(get_db)):
    """Get single product details."""
    product = db.query(Product).filter_by(product_id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "product_id": product.product_id,
        "product_name": product.product_name,
        "serial_number": product.serial_number,
        "product_status": product.product_status,
        "manufacturing_location": product.manufacturing_location,
        "intended_retailer": {
            "retailer_id": product.intended_retailer.retailer_id,
            "retailer_name": product.intended_retailer.retailer_name,
            "city": product.intended_retailer.city,
            "state": product.intended_retailer.state,
        }
        if product.intended_retailer
        else None,
        "warranty_registration": {
            "registration_id": product.warranty_registration.registration_id,
            "customer_name": product.warranty_registration.customer_name,
            "warranty_status": product.warranty_registration.warranty_status,
        }
        if product.warranty_registration
        else None,
    }


# ---------------------------------------------------------
# QR Code Retrieval & Download Endpoints
# ---------------------------------------------------------
@app.get("/api/products/{product_id}/qrs", tags=["QR Codes"])
def get_product_qrs_metadata(product_id: str, db: Session = Depends(get_db)):
    """Retrieve metadata and URLs for both external and internal QR codes of a product."""
    product = db.query(Product).filter_by(product_id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    ext_url = build_verification_url(product.external_qr_token)
    int_url = build_registration_url(product.internal_qr_token)

    return {
        "product_id": product.product_id,
        "product_name": product.product_name,
        "external_qr": {
            "purpose": "Pre-purchase Verification",
            "token": product.external_qr_token,
            "target_url": ext_url,
            "image_url": f"/api/products/{product.product_id}/qrs/external",
        },
        "internal_qr": {
            "purpose": "Post-purchase Warranty Registration",
            "token": product.internal_qr_token,
            "target_url": int_url,
            "image_url": f"/api/products/{product.product_id}/qrs/internal",
        },
    }


@app.get("/api/products/{product_id}/qrs/{qr_type}", tags=["QR Codes"])
def get_qr_image(
    product_id: str,
    qr_type: str,
    download: bool = Query(False, description="Download as attachment"),
    db: Session = Depends(get_db),
):
    """Serve the PNG QR code image for a product (external or internal)."""
    if qr_type not in {"external", "internal"}:
        raise HTTPException(status_code=400, detail="qr_type must be 'external' or 'internal'")

    product = db.query(Product).filter_by(product_id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    target_file = QR_STORAGE_DIR / f"{product_id}_{qr_type}_qr.png"

    # If image does not exist yet, generate on the fly
    if not target_file.exists():
        generate_product_qr_files(
            product_id=product.product_id,
            external_token=product.external_qr_token,
            internal_token=product.internal_qr_token,
        )

    filename = f"{product_id}_{qr_type}_qr.png"
    return FileResponse(
        path=str(target_file),
        media_type="image/png",
        filename=filename if download else None,
    )


# ---------------------------------------------------------
# Portal Landing Page
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse, tags=["Web UI"])
def home_portal(request: Request, db: Session = Depends(get_db)):
    """Demo portal overview showing products and interactive QR previews."""
    products = db.query(Product).order_by(Product.product_id).all()
    return templates.TemplateResponse(
        request,
        "index.html",
        {"products": products},
    )

