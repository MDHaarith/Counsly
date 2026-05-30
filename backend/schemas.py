from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from backend.community import normalize_community

# --- AUTH & USER SCHEMAS ---
class UserProfile(BaseModel):
    id: str
    name: Optional[str]
    google_email: Optional[str]
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

class ReorderItem(BaseModel):
    college_code: str = Field(..., max_length=50)
    branch_code: str = Field(..., max_length=50)
    priority: int = Field(..., ge=1, le=300)
    category: Optional[str] = Field("Moderate", max_length=50)
    notes: Optional[str] = Field(None, max_length=1024)

class ReorderRequest(BaseModel):
    priorities: List[ReorderItem]

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
    community: Optional[str] = None
    is_autonomous: Optional[bool] = None
    min_placement_rate: Optional[float] = None
    search: Optional[str] = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)

    @field_validator("community")
    @classmethod
    def normalize_requested_community(cls, value: Optional[str]) -> Optional[str]:
        return normalize_community(value) if value else value

class CollegeCompactResponse(BaseModel):
    code: str
    name: str
    district: str
    type: str
    is_autonomous: bool
    fee_structure_annual: Optional[int]
    placement_rate_pct: Optional[float]
    fit_score: float
    branch_code: Optional[str] = None
    branch_name: Optional[str] = None
    cutoff_mark_2025: Optional[float] = None
    cutoff_rank_2025: Optional[int] = None
    seats: Optional[int] = None

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
    nearest_railway_station_latitude: Optional[float] = None
    nearest_railway_station_longitude: Optional[float] = None
    nearest_railway_distance_km: Optional[float]
    nearest_express_station: Optional[str] = None
    nearest_express_station_latitude: Optional[float] = None
    nearest_express_station_longitude: Optional[float] = None
    nearest_express_station_distance_km: Optional[float] = None
    nearest_bus_station: Optional[str] = None
    nearest_bus_station_latitude: Optional[float] = None
    nearest_bus_station_longitude: Optional[float] = None
    nearest_bus_station_distance_km: Optional[float] = None
    nearest_bus_stop: Optional[str] = None
    nearest_bus_stop_latitude: Optional[float] = None
    nearest_bus_stop_longitude: Optional[float] = None
    nearest_bus_stop_distance_km: Optional[float] = None
    nearest_tfc: Optional[Dict[str, Any]] = None
    branches: List[Dict[str, Any]]  # List of branches and community seats
    cutoff_trends: Dict[str, List[CutoffTrend]]  # Map branch_code to list of historical cutoffs
    details_raw: Optional[str] = None

# --- COMPARE SCHEMAS ---
class CompareRequest(BaseModel):
    college_codes: List[str] = Field(..., min_length=2, max_length=4)
    branch_codes: List[str] = Field(..., min_length=1)
    community: Optional[str] = None

    @field_validator("community")
    @classmethod
    def normalize_requested_community(cls, value: Optional[str]) -> Optional[str]:
        return normalize_community(value) if value else value

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

# --- LOGGING SCHEMAS ---
class ClientErrorLogRequest(BaseModel):
    kind: str = Field(..., max_length=100)
    endpoint: Optional[str] = Field(None, max_length=2048)
    error_type: Optional[str] = Field(None, max_length=256)
    message: Optional[str] = Field(None, max_length=4096)
    stack: Optional[str] = Field(None, max_length=16384)
    status: Optional[int] = None
    timestamp: Optional[str] = Field(None, max_length=100)
    user_id_hash: Optional[str] = Field(None, max_length=128)

class ClientErrorLogResponse(BaseModel):
    accepted: bool
    id: int

class VerifyRollRequest(BaseModel):
    roll_number: str = Field(..., max_length=30)
