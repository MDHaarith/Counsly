from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import PaymentAuditLog
from backend.routes.payments import (
    build_payment_receipt,
    payment_event_already_processed,
    payment_order_belongs_to_user,
    season_expiry_date,
    verify_razorpay_signature,
)


def test_build_payment_receipt_keeps_source_and_user_traceable():
    receipt = build_payment_receipt("user-abcdef123456", "choices")

    assert receipt.startswith("counsly_choices_userabc")
    assert len(receipt) <= 40


def test_verify_razorpay_signature_matches_hmac_contract():
    assert verify_razorpay_signature(
        "order_123",
        "pay_123",
        "13f113268a0357923e6390e6773754dc39c991f05a999bcaf04c161c59aeaaf8",
        "secret",
    )


def test_season_expiry_date_uses_configured_iso_date():
    assert season_expiry_date("2026-09-30") == date(2026, 9, 30)


def test_payment_order_helpers_bind_verification_to_user_and_prevent_replay():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        session.add(PaymentAuditLog(id=1, user_id="user-1", event_type="order_created", razorpay_order="order_abc"))
        session.add(PaymentAuditLog(id=2, user_id="user-1", event_type="verified", razorpay_order="order_done", razorpay_payment="pay_done"))
        session.commit()

        assert payment_order_belongs_to_user(session, "user-1", "order_abc") is True
        assert payment_order_belongs_to_user(session, "user-2", "order_abc") is False
        assert payment_event_already_processed(session, "order_done", "pay_done") is True
        assert payment_event_already_processed(session, "order_abc", "pay_new") is False
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
