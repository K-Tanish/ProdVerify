from backend.app.models.manufacturer import Manufacturer
from backend.app.models.product import Product
from backend.app.services.token_service import (
    generate_secure_token,
    generate_product_token_pair,
    generate_unique_token,
    is_token_in_use,
)


def test_generate_secure_token_properties():
    """Verify cryptographic token output properties."""
    token = generate_secure_token(32)
    assert isinstance(token, str)
    assert len(token) > 30
    # URL safe characters
    for char in token:
        assert char.isalnum() or char in "-_"


def test_generate_product_token_pair(db_session):
    """Verify that generated product tokens are distinct and unique."""
    ext_token, int_token = generate_product_token_pair(db_session)
    assert ext_token != int_token
    assert len(ext_token) > 0
    assert len(int_token) > 0


def test_no_token_collisions_batch(db_session):
    """Verify that multiple generated tokens are all distinct."""
    generated_tokens = set()
    num_pairs = 25
    for _ in range(num_pairs):
        ext, int_ = generate_product_token_pair(db_session)
        assert ext not in generated_tokens
        assert int_ not in generated_tokens
        generated_tokens.add(ext)
        generated_tokens.add(int_)

    assert len(generated_tokens) == num_pairs * 2


def test_is_token_in_use_detection(db_session):
    """Verify detection of tokens in the database."""
    mfg = Manufacturer(manufacturer_name="Token Mfg")
    db_session.add(mfg)
    db_session.flush()

    prod = Product(
        product_id="P_TOK_TEST",
        product_name="Token Test Product",
        manufacturer_id=mfg.manufacturer_id,
        serial_number="SN-TOK-TEST",
        external_qr_token="KNOWN-EXT-TOKEN",
        internal_qr_token="KNOWN-INT-TOKEN",
    )
    db_session.add(prod)
    db_session.commit()

    assert is_token_in_use(db_session, "KNOWN-EXT-TOKEN") is True
    assert is_token_in_use(db_session, "KNOWN-INT-TOKEN") is True
    assert is_token_in_use(db_session, "UNUSED-RANDOM-TOKEN") is False
