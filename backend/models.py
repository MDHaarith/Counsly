import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date, ForeignKey, 
    Text, BigInteger, SmallInteger, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.database import Base

# Helper to support UUID columns on both PostgreSQL (UUID native) and SQLite (String fallback)
class SafeUUID(String):
    pass

# 2. Users Table
class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    auth_user_id = Column(String(36), unique=True, nullable=False)
    google_id = Column(String(100))
    google_email = Column(String(200))
    name = Column(String(100))
    subscription_active = Column(Boolean, default=False)
    subscription_expiry = Column(Date)
    razorpay_payment_id = Column(String(100))
    welcome_message_sent = Column(Boolean, default=False)
    roll_number = Column(String(20))
    roll_number_verified = Column(Boolean, default=False)
    device_fingerprint_hash = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", uselist=False, back_populates="user", cascade="all, delete-orphan")

# 3. Workspaces Table (Strictly Private Personal Data Environment)
class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    slug = Column(String(80), unique=True)
    onboarding_step = Column(String(40), default="marks")
    onboarding_completed = Column(Boolean, default=False)
    onboarding_completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="workspace")
    settings = relationship("WorkspaceSettings", uselist=False, back_populates="workspace", cascade="all, delete-orphan")
    preferences = relationship("UserCollegePreference", back_populates="workspace", cascade="all, delete-orphan")

# 4. Workspace Settings Table
class WorkspaceSettings(Base):
    __tablename__ = "workspace_settings"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), unique=True, nullable=False)
    default_district = Column(String(100))
    preferred_branch_defaults = Column(Text)  # Stored as comma-separated list of codes
    phase_preferences = Column(Text)  # JSON structure
    saved_filters = Column(Text)  # JSON structure
    compact_view = Column(Boolean, default=False)
    mobile_density = Column(String(20), default="default")
    theme_mode = Column(String(20), default="mild")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="settings")

# 5. Workspace Activity Timeline
class WorkspaceActivity(Base):
    __tablename__ = "workspace_activity"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(80), nullable=False)
    entity_type = Column(String(80))
    entity_id = Column(String(100))
    summary = Column(Text, nullable=False)
    activity_metadata = Column("metadata", Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

# 6. Shortlist Snapshots Table
class ShortlistSnapshot(Base):
    __tablename__ = "shortlist_snapshots"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(120), nullable=False)
    source_group = Column(String(40), default="primary")
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("ShortlistSnapshotItem", back_populates="snapshot", cascade="all, delete-orphan")

# 7. Shortlist Snapshot Items
class ShortlistSnapshotItem(Base):
    __tablename__ = "shortlist_snapshot_items"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(36), ForeignKey("shortlist_snapshots.id", ondelete="CASCADE"), nullable=False)
    priority = Column(SmallInteger, nullable=False)
    college_code = Column(String(10), nullable=False)
    branch_code = Column(String(10), nullable=False)
    category = Column(String(20))
    notes = Column(Text)

    snapshot = relationship("ShortlistSnapshot", back_populates="items")

# 8. User College Preferences (Canonical Choice Filing Surface)
class UserCollegePreference(Base):
    __tablename__ = "user_college_preferences"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    preference_group = Column(String(40), default="primary")
    priority = Column(SmallInteger, nullable=False)
    college_code = Column(String(10), nullable=False)
    branch_code = Column(String(10))
    category = Column(String(20))
    category_override = Column(Boolean, default=False)
    notes = Column(Text)
    added_from = Column(String(20), default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="preferences")
    
    __table_args__ = (
        UniqueConstraint('workspace_id', 'preference_group', 'priority', name='uq_workspace_pref_priority'),
    )

# 9. TFC Locations Table
class TFCLocation(Base):
    __tablename__ = "tfc_locations"
    tfc_id = Column(BigInteger, primary_key=True, autoincrement=True)
    centre_name = Column(String(200), nullable=False)
    district = Column(String(100), nullable=False)
    address = Column(Text)
    phone = Column(String(50))
    latitude = Column(Float)
    longitude = Column(Float)
    google_maps_url = Column(Text)

# 11. Colleges Master Table
class College(Base):
    __tablename__ = "colleges"
    code = Column(String(10), primary_key=True)
    name = Column(String(250), nullable=False)
    district = Column(String(100), nullable=False)
    type = Column(String(80), nullable=False)
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    hostel_available = Column(Boolean, default=False)
    transport_available = Column(Boolean, default=False)
    website = Column(Text)
    is_autonomous = Column(Boolean, default=False)
    nba_accredited = Column(Boolean, default=False)
    coordinates_approximate = Column(Boolean, default=False)
    nearest_railway_station = Column(String(150))
    nearest_railway_distance_km = Column(Float)
    fee_structure_annual = Column(Integer)
    placement_rate_pct = Column(Float)
    avg_package_lpa = Column(Float)
    details_raw = Column(Text)

# 12. Branches Master Table
class Branch(Base):
    __tablename__ = "branches"
    code = Column(String(10), primary_key=True)
    name = Column(String(200), nullable=False)
    duration_years = Column(SmallInteger, default=4)

# 13. College-Branch Mapping
class CollegeBranch(Base):
    __tablename__ = "college_branches"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    college_code = Column(String(10), ForeignKey("colleges.code", ondelete="CASCADE"), nullable=False)
    branch_code = Column(String(10), ForeignKey("branches.code", ondelete="CASCADE"), nullable=False)
    approved_intake = Column(Integer)
    year_starting = Column(Integer)
    nba_accredited = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint('college_code', 'branch_code', name='uq_college_branch'),
    )

# 14. Seat Matrix per Community
class CommunitySeat(Base):
    __tablename__ = "community_seats"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    college_code = Column(String(10), ForeignKey("colleges.code", ondelete="CASCADE"), nullable=False)
    branch_code = Column(String(10), ForeignKey("branches.code", ondelete="CASCADE"), nullable=False)
    oc = Column(Integer, default=0)
    bc = Column(Integer, default=0)
    bcm = Column(Integer, default=0)
    mbc = Column(Integer, default=0)
    sc = Column(Integer, default=0)
    sca = Column(Integer, default=0)
    st = Column(Integer, default=0)
    total = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint('college_code', 'branch_code', name='uq_community_seats_cb'),
    )

# 15. Historical and Active Cutoff Data Table
class CutoffData(Base):
    __tablename__ = "cutoff_data"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    college_code = Column(String(10), ForeignKey("colleges.code", ondelete="CASCADE"), nullable=False)
    branch_code = Column(String(10), ForeignKey("branches.code", ondelete="CASCADE"), nullable=False)
    community = Column(String(10), nullable=False)
    year = Column(SmallInteger, nullable=False)
    round_number = Column(SmallInteger, nullable=False)
    cutoff_mark = Column(Float, nullable=False)
    cutoff_rank = Column(Integer)
    seats_allotted = Column(Integer, default=0)

# 16. Official TNEA Roll Numbers List
class TNEARollNumber(Base):
    __tablename__ = "tnea_roll_numbers"
    roll_number = Column(String(30), primary_key=True)
    student_name = Column(String(150), nullable=False)
    community = Column(String(10), nullable=False)
    district = Column(String(100), nullable=False)
    total_marks = Column(Float, nullable=False)
    official_rank = Column(Integer, nullable=False)
    random_number = Column(String(30))
    board = Column(String(30))

# 17. Counselling Round Dates Table
class RoundDate(Base):
    __tablename__ = "round_dates"
    round_number = Column(SmallInteger, primary_key=True)
    choice_start = Column(DateTime)
    choice_end = Column(DateTime)
    allotment = Column(DateTime)
    confirm_start = Column(DateTime)
    confirm_end = Column(DateTime)
    reporting_end = Column(DateTime)

# 18. Ingestion Audit Log
class IngestionAuditLog(Base):
    __tablename__ = "ingestion_audit_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dataset = Column(String(80), nullable=False)
    source = Column(Text)
    rows_inserted = Column(Integer, default=0)
    rows_updated = Column(Integer, default=0)
    rows_rejected = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    status = Column(String(20), nullable=False)
    error_message = Column(Text)

# 19. Data Freshness Tracking
class DataFreshness(Base):
    __tablename__ = "data_freshness"
    dataset_key = Column(String(80), primary_key=True)
    last_refreshed = Column(DateTime, nullable=False)
    row_count = Column(Integer)
    notes = Column(Text)

# 20. Admin Manual Update Log
class AdminUpdateLog(Base):
    __tablename__ = "admin_update_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dataset = Column(String(80), nullable=False)
    source_url = Column(Text)
    rows_inserted = Column(Integer, default=0)
    rows_updated = Column(Integer, default=0)
    rows_rejected = Column(Integer, default=0)
    status = Column(String(40), default="needs_review")
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 21. Scraping Automation Jobs
class ScrapingJob(Base):
    __tablename__ = "scraping_jobs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dataset = Column(String(80), nullable=False)
    source_url = Column(Text)
    job_type = Column(String(40), default="real_time_scraping")
    status = Column(String(40), nullable=False)
    row_count = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# 22. AI Guidance Audit Log
class AIGuidanceLog(Base):
    __tablename__ = "ai_guidance_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"))
    feature = Column(String(40), nullable=False)
    ai_available = Column(Boolean, default=False)
    prompt_context = Column(Text)
    response_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# 23. Payment Audit Log
class PaymentAuditLog(Base):
    __tablename__ = "payment_audit_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    event_type = Column(String(40), nullable=False)
    razorpay_order = Column(String(100))
    razorpay_payment = Column(String(100))
    amount_paise = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# 24. Client Error Log
class ClientErrorLog(Base):
    __tablename__ = "client_error_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    kind = Column(String(40), nullable=False)
    endpoint = Column(String(240))
    error_type = Column(String(120))
    message = Column(Text)
    stack = Column(Text)
    status_code = Column(Integer)
    user_id_hash = Column(String(64))
    reported_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

# 25. Compare History
class CollegeCompareHistory(Base):
    __tablename__ = "college_compare_history"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    session_name = Column(String(120))
    college_codes = Column(Text, nullable=False)
    branch_codes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    saved = Column(Boolean, default=False)

# 26. Rounds Checklist Tracker Progress
class RoundChecklistProgress(Base):
    __tablename__ = "round_checklist_progress"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    round_number = Column(SmallInteger, nullable=False)
    step_1_completed = Column(Boolean, default=False)
    step_2_completed = Column(Boolean, default=False)
    step_3_completed = Column(Boolean, default=False)
    step_4_completed = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('workspace_id', 'round_number', name='uq_workspace_round'),
    )

# 27. Device Fingerprints Abuse Layer
class DeviceFingerprint(Base):
    __tablename__ = "device_fingerprints"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fingerprint_hash = Column(String(64), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('fingerprint_hash', 'user_id', name='uq_device_fingerprint_user'),
    )

# 28. Subscriptions Ledger Table
class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
