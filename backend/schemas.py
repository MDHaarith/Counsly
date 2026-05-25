from pydantic import BaseModel, Field, EmailStr
from typing import Any, Dict, List, Optional
from datetime import datetime, date

# --- AUTH & USER SCHEMAS ---
class UserProfile(BaseModel):
    id: str
    name: Optional[str]
    google_email: Optional[str]
    subscription_active: bool
    subscription_expiry: Optional[date]
    welcome_message_sent: bool
    roll_number: Optional[str]
    roll_number_verified: bool

    model_config = {
        "from_attributes": True
    }

class SessionRequest(BaseModel):
    google_email: EmailStr
    name: str
    google_id: Optional[str] = None
    google_id_token: Optional[str] = None
    device_fingerprint_hash: Optional[str] = None

# --- ONBOARDING & GUIDANCE SCHEMAS ---
class MarksInput(BaseModel):
    maths: int = Field(..., ge=0, le=100, description="Maths marks (0-100)")
    physics: int = Field(..., ge=0, le=50, description="Physics marks (0-50)")
    chemistry: int = Field(..., ge=0, le=50, description="Chemistry marks (0-50)")

class OnboardingRequest(BaseModel):
    maths: int = Field(..., ge=0, le=100)
    physics: int = Field(..., ge=0, le=50)
    chemistry: int = Field(..., ge=0, le=50)
    default_district: Optional[str] = None
    preferred_branches: List[str] = []

class OnboardingResponse(BaseModel):
    eligible: bool
    message: str
    onboarding_completed: bool

class AIGuidanceRequest(BaseModel):
    marks_total: Optional[float] = None
    community: Optional[str] = "OC"
    district: Optional[str] = None
    preferred_branches: List[str] = []

class AIGuidanceResponse(BaseModel):
    ai_available: bool
    strategy_note: str
    confidence_label: str
    next_action: str

# --- CHOICES & PREFERENCES SCHEMAS ---
class ChoiceItemBase(BaseModel):
    college_code: str
    branch_code: str
    priority: int = Field(..., ge=1, le=300)
    category: Optional[str] = None  # 'Safe', 'Moderate', 'Ambitious'
    notes: Optional[str] = None

class ChoiceItemCreate(ChoiceItemBase):
    pass

class ChoiceItemResponse(ChoiceItemBase):
    id: int
    college_name: str
    branch_name: str
    fee_structure_annual: Optional[int] = None
    placement_rate_pct: Optional[float] = None
    cutoff_mark_2025: Optional[float] = None
    cutoff_rank_2025: Optional[int] = None

    model_config = {
        "from_attributes": True
    }

class ReorderRequest(BaseModel):
    priorities: List[Dict[str, Any]]  # List containing dictionary keys of: college_code, branch_code, new_priority

class SnapshotCreate(BaseModel):
    title: str

class SnapshotResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    item_count: int

    model_config = {
        "from_attributes": True
    }

# --- WORKSPACE SETTINGS SCHEMAS ---
class WorkspaceSettingsUpdate(BaseModel):
    default_district: Optional[str] = None
    preferred_branches: List[str] = []
    compact_view: bool = False
    mobile_density: str = "default"
    theme_mode: str = "mild"

class WorkspaceSettingsResponse(WorkspaceSettingsUpdate):
    saved_filters: Optional[str] = None
    phase_preferences: Optional[str] = None

# --- EXPLORE SCHEMAS ---
class CollegeSearchQuery(BaseModel):
    district: Optional[str] = None
    type: Optional[str] = None  # 'Govt', 'Aided', 'Self-Finance'
    branch_code: Optional[str] = None
    is_autonomous: Optional[bool] = None
    min_placement_rate: Optional[float] = None
    search: Optional[str] = None
    limit: int = 50
    offset: int = 0

class CollegeCompactResponse(BaseModel):
    code: str
    name: str
    district: str
    type: str
    is_autonomous: bool
    fee_structure_annual: Optional[int]
    placement_rate_pct: Optional[float]
    fit_score: float

class CutoffTrend(BaseModel):
    year: int
    cutoff_mark: float
    cutoff_rank: Optional[int]
    seats_allotted: int

class CollegeDetailResponse(BaseModel):
    code: str
    name: str
    district: str
    type: str
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    hostel_available: bool
    transport_available: bool
    website: Optional[str]
    is_autonomous: bool
    nba_accredited: bool
    fee_structure_annual: Optional[int]
    placement_rate_pct: Optional[float]
    avg_package_lpa: Optional[float]
    nearest_railway_station: Optional[str]
    nearest_railway_distance_km: Optional[float]
    nearest_tfc: Optional[Dict[str, Any]] = None
    branches: List[Dict[str, Any]]  # List of branches and community seats
    cutoff_trends: Dict[str, List[CutoffTrend]]  # Map branch_code to list of historical cutoffs

# --- COMPARE SCHEMAS ---
class CompareRequest(BaseModel):
    college_codes: List[str]
    branch_codes: List[str]

class CollegeCompareColumn(BaseModel):
    code: str
    name: str
    type: str
    fee_structure_annual: Optional[int]
    placement_rate_pct: Optional[float]
    avg_package_lpa: Optional[float]
    district: str
    is_autonomous: bool
    nba_accredited: bool
    hostel_available: bool = False
    transport_available: bool = False
    nearest_railway_station: Optional[str] = None
    nearest_railway_distance_km: Optional[float] = None
    cutoff_2025: Optional[float] = None
    cutoff_rank_2025: Optional[int] = None
    cutoff_marks_last_three: List[float] = []

class CompareResponse(BaseModel):
    colleges: List[CollegeCompareColumn]
    explanation: str

class AICompareRequest(BaseModel):
    colleges: List[str]
    metrics: List[str] = []

class AICompareResponse(BaseModel):
    ai_available: bool
    headline: str
    reasoning: str

class CompareSessionCreate(BaseModel):
    session_name: str
    college_codes: List[str]
    branch_codes: List[str] = []

class CompareSessionResponse(CompareSessionCreate):
    id: int
    created_at: datetime
    saved: bool

    model_config = {
        "from_attributes": True
    }

# --- SUBSCRIPTION SCHEMAS ---
class PaymentOrderRequest(BaseModel):
    source: Optional[str] = None

class RazorpayOrderResponse(BaseModel):
    id: str
    amount: int
    currency: str
    receipt: str
    key_id: Optional[str] = None

class PaymentVerificationRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class PaymentVerificationResponse(BaseModel):
    success: bool
    message: str
    subscription_active: bool
    subscription_expiry: Optional[date]

# --- ROUNDS / OPERATIONS SCHEMAS ---
class RoundStatusResponse(BaseModel):
    round_number: int
    choice_start: Optional[datetime]
    choice_end: Optional[datetime]
    allotment: Optional[datetime]
    confirm_start: Optional[datetime]
    confirm_end: Optional[datetime]
    reporting_end: Optional[datetime]
    active_phase: str
    seconds_remaining: int
    phase: Dict[str, Any]
    checklist: Dict[str, bool]

class DecisionConfirmationRequest(BaseModel):
    decision_type: str

class DecisionConfirmationResponse(BaseModel):
    success: bool
    message: str
    tfc_required: bool
    nearest_tfc: Optional[Dict[str, Any]] = None

class AdminUpdateRequest(BaseModel):
    dataset: str
    source_url: Optional[str] = None
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_rejected: int = 0

class AdminUpdateResponse(BaseModel):
    dataset: str
    source_url: Optional[str] = None
    rows_inserted: int
    rows_updated: int
    rows_rejected: int
    status: str
    summary: str

class ScrapingJobRequest(BaseModel):
    dataset: str
    source_url: Optional[str] = None
    status: str = "queued"
    row_count: int = 0
    error_message: Optional[str] = None

class ScrapingJobResponse(BaseModel):
    dataset: str
    source_url: Optional[str] = None
    job_type: str
    status: str
    row_count: int
    error_message: Optional[str] = None

class OperationalStatusResponse(BaseModel):
    admin_updates: List[AdminUpdateResponse]
    scraping_jobs: List[ScrapingJobResponse]
    ai: Dict[str, bool]

# --- LOGGING SCHEMAS ---
class ClientErrorLogRequest(BaseModel):
    kind: str
    endpoint: Optional[str] = None
    error_type: Optional[str] = None
    message: Optional[str] = None
    stack: Optional[str] = None
    status: Optional[int] = None
    timestamp: Optional[str] = None
    user_id_hash: Optional[str] = None

class ClientErrorLogResponse(BaseModel):
    accepted: bool
    id: int
