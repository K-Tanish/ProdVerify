from pathlib import Path
from typing import Optional
import qrcode
from PIL import Image

from backend.app.config import BASE_VERIFY_URL, QR_STORAGE_DIR


def build_verification_url(token: str, base_url: Optional[str] = None) -> str:
    """Build the public URL for external pre-purchase product verification."""
    root = (base_url or BASE_VERIFY_URL).rstrip("/")
    return f"{root}/verify/{token}"


def build_registration_url(token: str, base_url: Optional[str] = None) -> str:
    """Build the public URL for internal post-purchase warranty registration."""
    root = (base_url or BASE_VERIFY_URL).rstrip("/")
    return f"{root}/register/{token}"


def generate_qr_image(payload: str) -> Image.Image:
    """Generate a Pillow QR code image from the payload."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img.get_image() if hasattr(img, "get_image") else img


def save_qr_code(payload: str, filepath: Path) -> Path:
    """Generate and persist a QR code image to the specified path."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    img = generate_qr_image(payload)
    img.save(str(filepath))
    return filepath


def generate_product_qr_files(
    product_id: str,
    external_token: str,
    internal_token: str,
    output_dir: Optional[Path] = None,
    base_url: Optional[str] = None,
) -> tuple[Path, Path]:
    """Generate and save both external and internal QR images for a product."""
    target_dir = Path(output_dir or QR_STORAGE_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)

    ext_url = build_verification_url(external_token, base_url=base_url)
    int_url = build_registration_url(internal_token, base_url=base_url)

    ext_path = target_dir / f"{product_id}_external_qr.png"
    int_path = target_dir / f"{product_id}_internal_qr.png"

    save_qr_code(ext_url, ext_path)
    save_qr_code(int_url, int_path)

    return ext_path, int_path
