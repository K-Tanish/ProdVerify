from pathlib import Path
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import uuid
from backend.app.config import BASE_VERIFY_URL, QR_STORAGE_DIR
from backend.app.database import get_db
from backend.app.models.product import Product
from backend.app.models.retailer import Retailer
from backend.app.models.scan_history import ScanHistory
from backend.app.models.warranty_registration import WarrantyRegistration
from backend.app.models.manufacturer import Manufacturer
from backend.app.services.token_service import generate_product_token_pair
from backend.app.services.qr_service import (
    build_registration_url,
    build_verification_url,
    generate_product_qr_files,
)
from backend.app.services.verification_service import verify_external_token

from pydantic import BaseModel
from backend.app.services.registration_service import (
    RegistrationError,
    register_warranty,
    resolve_internal_token,
)

class WarrantyRegisterPayload(BaseModel):
    customer_name: str
    email: str
    retailer_id: int
    purchase_price: Optional[float] = None
    purchase_date: str

class ProductCreatePayload(BaseModel):
    product_name: str
    intended_retailer_id: int
    serial_number: Optional[str] = None
    manufacturing_location: Optional[str] = None
    product_id: Optional[str] = None
    manufacturer_id: Optional[int] = None


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


@app.get("/register/{token}", response_class=HTMLResponse, tags=["Web UI"])
def view_registration_page(request: Request, token: str):
    """Render customer-facing post-purchase warranty registration page."""
    return templates.TemplateResponse(
        request,
        "register.html",
        {"token": token},
    )


@app.get("/api/register/{token}", tags=["Registration"])
def api_get_registration_info(token: str, db: Session = Depends(get_db)):
    """Resolve internal token and verify product eligibility for warranty registration."""
    try:
        return resolve_internal_token(db, token)
    except RegistrationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@app.post("/api/register/{token}", tags=["Registration"])
def api_register_warranty(
    token: str,
    payload: WarrantyRegisterPayload,
    db: Session = Depends(get_db),
):
    """Register customer warranty, mark product SOLD, and record event in Scan_History atomically."""
    try:
        return register_warranty(
            session=db,
            token=token,
            customer_name=payload.customer_name,
            email=payload.email,
            retailer_id=payload.retailer_id,
            purchase_price=payload.purchase_price,
            purchase_date=payload.purchase_date,
        )
    except RegistrationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)




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
            "external_qr_token": p.external_qr_token,
            "internal_qr_token": p.internal_qr_token,
            "registration_status": "REGISTERED" if p.warranty_registration else "UNREGISTERED",
            "intended_retailer": {
                "retailer_id": p.intended_retailer.retailer_id,
                "retailer_name": p.intended_retailer.retailer_name,
                "city": p.intended_retailer.city,
                "state": p.intended_retailer.state,
            }
            if p.intended_retailer
            else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in products
    ]


@app.post("/api/products", tags=["Products"])
def create_product(payload: ProductCreatePayload, db: Session = Depends(get_db)):
    """Create a new product with two cryptographically secure QR tokens and generated QR images."""
    # 1. Retailer check
    ret = db.query(Retailer).filter_by(retailer_id=payload.intended_retailer_id).first()
    if not ret:
        raise HTTPException(status_code=404, detail="Selected retailer not found")

    # 2. Manufacturer check
    mfg_id = payload.manufacturer_id
    if not mfg_id:
        mfg = db.query(Manufacturer).filter_by(status="ACTIVE").first()
        if not mfg:
            raise HTTPException(status_code=400, detail="No active manufacturer found")
        mfg_id = mfg.manufacturer_id

    # 3. Product ID generation if not provided
    prod_id = payload.product_id
    if not prod_id:
        count = db.query(Product).count() + 1
        prod_id = f"PROD-{count:03d}"
        while db.query(Product).filter_by(product_id=prod_id).first():
            prod_id = f"PROD-{uuid.uuid4().hex[:6].upper()}"
    else:
        if db.query(Product).filter_by(product_id=prod_id).first():
            raise HTTPException(status_code=409, detail=f"Product ID '{prod_id}' already exists")

    # 4. Serial number generation if not provided
    sn = payload.serial_number
    if not sn:
        sn = f"SN-{prod_id}-{uuid.uuid4().hex[:4].upper()}"
    else:
        if db.query(Product).filter_by(serial_number=sn).first():
            raise HTTPException(status_code=409, detail=f"Serial number '{sn}' already exists")

    # 5. Generate secure tokens
    ext_token, int_token = generate_product_token_pair(db)

    new_prod = Product(
        product_id=prod_id.strip(),
        product_name=payload.product_name.strip(),
        manufacturer_id=mfg_id,
        serial_number=sn.strip(),
        external_qr_token=ext_token,
        internal_qr_token=int_token,
        manufacturing_location=payload.manufacturing_location.strip() if payload.manufacturing_location else None,
        intended_retailer_id=ret.retailer_id,
        product_status="IN_STOCK",
    )
    db.add(new_prod)
    db.commit()

    # Generate QR images
    generate_product_qr_files(
        product_id=new_prod.product_id,
        external_token=new_prod.external_qr_token,
        internal_token=new_prod.internal_qr_token,
    )

    return {
        "success": True,
        "product_id": new_prod.product_id,
        "product_name": new_prod.product_name,
        "serial_number": new_prod.serial_number,
        "product_status": new_prod.product_status,
        "external_qr_token": new_prod.external_qr_token,
        "internal_qr_token": new_prod.internal_qr_token,
        "intended_retailer": {
            "retailer_id": ret.retailer_id,
            "retailer_name": ret.retailer_name,
        },
    }


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
        "external_qr_token": product.external_qr_token,
        "internal_qr_token": product.internal_qr_token,
        "registration_status": "REGISTERED" if product.warranty_registration else "UNREGISTERED",
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
# Dashboard Metrics & History Endpoints
# ---------------------------------------------------------
@app.get("/api/dashboard/stats", tags=["Dashboard"])
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Retrieve real-time metrics derived from database tables."""
    total_products = db.query(Product).count()
    in_stock = db.query(Product).filter_by(product_status="IN_STOCK").count()
    sold = db.query(Product).filter_by(product_status="SOLD").count()
    blocked = db.query(Product).filter_by(product_status="BLOCKED").count()
    active_warranties = db.query(WarrantyRegistration).filter_by(warranty_status="ACTIVE").count()
    total_external_scans = db.query(ScanHistory).filter_by(scan_type="EXTERNAL_VERIFICATION").count()
    suspicious_scans = db.query(ScanHistory).filter_by(result="SUSPICIOUS").count()
    invalid_scans = db.query(ScanHistory).filter_by(result="INVALID").count()

    return {
        "total_products": total_products,
        "in_stock_products": in_stock,
        "sold_products": sold,
        "blocked_products": blocked,
        "active_warranties": active_warranties,
        "total_external_scans": total_external_scans,
        "suspicious_scans": suspicious_scans,
        "invalid_scans": invalid_scans,
        "total_suspicious_events": suspicious_scans + invalid_scans + blocked,
    }


@app.get("/api/scans", tags=["Scans"])
def list_scans(
    limit: int = Query(100, ge=1, le=500),
    result: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List recent scan events from Scan_History."""
    query = db.query(ScanHistory)
    if result:
        query = query.filter_by(result=result)
    if product_id:
        query = query.filter_by(product_id=product_id)

    scans = query.order_by(ScanHistory.scanned_at.desc()).limit(limit).all()
    return [
        {
            "scan_id": s.scan_id,
            "product_id": s.product_id,
            "product_name": s.product.product_name if s.product else None,
            "scan_type": s.scan_type,
            "scanned_at": s.scanned_at.isoformat() if s.scanned_at else None,
            "scan_location": s.scan_location,
            "result": s.result,
            "risk_reason": s.risk_reason,
        }
        for s in scans
    ]


@app.get("/api/warranties", tags=["Warranties"])
def list_warranties(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all registered warranties from Warranty_Registrations."""
    query = db.query(WarrantyRegistration)
    if status:
        query = query.filter_by(warranty_status=status)

    warranties = query.order_by(WarrantyRegistration.created_at.desc()).all()
    return [
        {
            "registration_id": w.registration_id,
            "product_id": w.product_id,
            "product_name": w.product.product_name if w.product else None,
            "serial_number": w.product.serial_number if w.product else None,
            "customer_name": w.customer_name,
            "email": w.email,
            "retailer": {
                "retailer_id": w.retailer.retailer_id,
                "retailer_name": w.retailer.retailer_name,
                "city": w.retailer.city,
                "state": w.retailer.state,
            }
            if w.retailer
            else None,
            "purchase_price": w.purchase_price,
            "purchase_date": str(w.purchase_date),
            "warranty_status": w.warranty_status,
            "warranty_start_date": str(w.warranty_start_date),
            "warranty_end_date": str(w.warranty_end_date),
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in warranties
    ]



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

