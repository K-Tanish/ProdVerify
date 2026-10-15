import secrets
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.models.product import Product


def generate_secure_token(nbytes: int = 32) -> str:
    """Generate a cryptographically secure, URL-safe random token."""
    return secrets.token_urlsafe(nbytes)


def is_token_in_use(session: Session, token: str) -> bool:
    """Check if a token is already assigned as external or internal QR token in Products."""
    existing = session.query(Product).filter(
        or_(
            Product.external_qr_token == token,
            Product.internal_qr_token == token,
        )
    ).first()
    return existing is not None


def generate_unique_token(session: Session, nbytes: int = 32, max_retries: int = 100) -> str:
    """Generate a cryptographically secure token guaranteed to be unique in the database."""
    for _ in range(max_retries):
        token = generate_secure_token(nbytes)
        if not is_token_in_use(session, token):
            return token
    raise RuntimeError("Failed to generate a unique token after maximum retries.")


def generate_product_token_pair(session: Session, nbytes: int = 32) -> tuple[str, str]:
    """
    Generate two distinct, cryptographically secure, database-unique tokens:
    one for external QR verification and one for internal QR warranty registration.
    """
    external_token = generate_unique_token(session, nbytes=nbytes)

    # Ensure internal token is unique in DB and distinct from external_token
    for _ in range(100):
        internal_token = generate_unique_token(session, nbytes=nbytes)
        if internal_token != external_token:
            return external_token, internal_token

    raise RuntimeError("Failed to generate a distinct internal token after retries.")
