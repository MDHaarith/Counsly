from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import DeviceFingerprint


def test_device_fingerprint_allows_multiple_users_but_blocks_duplicate_user_pair():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        session.add(DeviceFingerprint(id=1, fingerprint_hash="fp-123", user_id="user-1"))
        session.add(DeviceFingerprint(id=2, fingerprint_hash="fp-123", user_id="user-2"))
        session.commit()

        session.add(DeviceFingerprint(id=3, fingerprint_hash="fp-123", user_id="user-1"))
        try:
            session.commit()
            assert False, "duplicate fingerprint/user pair should fail"
        except IntegrityError:
            session.rollback()
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
