"""Pydantic request and response models for Counsly API."""

from typing import Literal

from pydantic import BaseModel, Field

Community = Literal["OC", "BC", "BCM", "MBC", "SC", "ST"]
Board = Literal["State", "CBSE", "ICSE"]
SafetyCategory = Literal["safe", "moderate", "ambitious"]
FreshnessStatus = Literal["missing", "seeded_unverified", "verified", "stale", "disabled"]


class SessionUser(BaseModel):
    app_user_id: str
    workspace_id: str
    email: str
    display_name: str | None = None
    paid: bool = False


class RoundDateResponse(BaseModel):
    round_number: int
    date: str


class AppConfigResponse(BaseModel):
    tnea_phase: int
    total_rounds: int
    rank_released: bool
    roll_data_ready: bool
    rank_lookup_ready: bool
    free_chat_limit: int
    season_end_date: str | None
    round_dates: list[RoundDateResponse]
    data_freshness: dict[str, FreshnessStatus]


class MarksRequest(BaseModel):
    maths_mark: int = Field(ge=0, le=100)
    physics_mark: int = Field(ge=0, le=100)
    chemistry_mark: int = Field(ge=0, le=100)


class DetailsRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    board: Board
    district: str = Field(min_length=1, max_length=80)
    home_district: str = Field(min_length=1, max_length=80)
    community_quota: Community


class OnboardingResponse(BaseModel):
    workspace_id: str
    current_step: int
    is_complete: bool
    eligible: bool | None
    eligibility_reason: str | None
    cutoff_mark: int | None


class RankBandResponse(BaseModel):
    maths_mark: int
    physics_mark: int
    chemistry_mark: int
    rank_min: int | None
    rank_max: int | None
    confidence_label: Literal["High", "Medium", "Low"] | None
    sample_size: int | None
    source_years: list[int]
    is_abstain: bool
    disclaimer: str
    model_version: str | None = None
    data_source: Literal["ml_prediction", "historical"] = "historical"


class RecommendationResponse(BaseModel):
    college_code: str
    college_name: str
    branch_code: str
    branch_name: str
    district: str | None
    cutoff_rank: int | None
    prediction_lower: int | None = None
    prediction_upper: int | None = None
    prediction_confidence: Literal["High", "Medium", "Low"] | None = None
    model_version: str | None = None
    data_source: Literal["ml_prediction", "historical"] = "historical"
    safety: SafetyCategory | None
    season_year: int | None
    is_locked: bool = False


class RecommendationsEnvelope(BaseModel):
    items: list[RecommendationResponse]
    total: int
    returned: int
    paid: bool
    restriction: Literal["plan_limit", "data_not_ready", "ineligible"] | None = None


class ChoiceCreateRequest(BaseModel):
    college_code: str = Field(min_length=1, max_length=20)
    branch_code: str = Field(min_length=1, max_length=20)
    notes: str | None = Field(default=None, max_length=600)
    manual_category: SafetyCategory | None = None


class ChoiceMoveRequest(BaseModel):
    priority: int = Field(ge=1, le=200)


class ChoiceUpdateRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=600)
    manual_category: SafetyCategory | None = None


class ChoiceResponse(BaseModel):
    id: str
    priority: int
    college_code: str
    college_name: str | None
    branch_code: str
    branch_name: str | None
    district: str | None
    system_category: SafetyCategory | None
    manual_category: SafetyCategory | None
    notes: str | None


class ChoicesEnvelope(BaseModel):
    items: list[ChoiceResponse]
    limit: int
    paid: bool


class PaymentOrderResponse(BaseModel):
    order_id: str
    amount_paise: int
    currency: str
    key_id: str


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentVerifyResponse(BaseModel):
    active: bool
    status: str


class ProfileResponse(BaseModel):
    workspace_id: str
    full_name: str | None
    board: str | None
    district: str | None
    home_district: str | None
    community_quota: Community | None
    maths_mark: int | None
    physics_mark: int | None
    chemistry_mark: int | None
    cutoff_mark: int | None
    official_rank: int | None
    paid: bool


class ExploreCollegeResponse(BaseModel):
    college_code: str
    college_name: str
    district: str | None
    autonomous_status: str | None
    hostel_boys: bool | None
    hostel_girls: bool | None
    transport_facilities: bool | None
    latitude: float | None
    longitude: float | None


class ExploreEnvelope(BaseModel):
    items: list[ExploreCollegeResponse]
    total: int


class CollegeBranchInsight(BaseModel):
    branch_code: str
    branch_name: str
    total_seats: int | None = None


class CollegeDetailResponse(ExploreCollegeResponse):
    address: str | None
    website: str | None
    email: str | None
    branches: list[CollegeBranchInsight]
