export type Community = "OC" | "BC" | "BCM" | "MBC" | "SC" | "SCA" | "ST";
export type Board = "State" | "CBSE" | "ICSE";
export type SafetyLabel = "safe" | "moderate" | "ambitious";
export type AccessTier = "free" | "paid";
export type RestrictionReason = "plan_limit" | "tnea_phase" | "data_not_ready";
export type TNEAPhase = 1 | 2 | 3 | 4 | 5;

export interface StudentProfile {
  id: string;
  workspaceId: string;
  fullName: string;
  email: string;
  maths: number;
  physics: number;
  chemistry: number;
  total: number;
  aggregate: number;
  community: Community;
  district: string;
  homeDistrict: string;
  board: Board;
  rankMin: number | null;
  rankMax: number | null;
  rankConfidence: "High" | "Medium" | "Low" | null;
  onboardingComplete: boolean;
}

export type OnboardingStep = "marks" | "details" | "rank";

export interface OnboardingState {
  currentStep: OnboardingStep;
  completed: boolean;
}

export interface College {
  code: string;
  name: string;
  district: string;
  type: string;
  isAutonomous: boolean;
  hasHostel: boolean;
  address: string | null;
  lat: number | null;
  lng: number | null;
}

export interface Branch {
  code: string;
  name: string;
}

export interface CollegeBranch {
  collegeCode: string;
  branchCode: string;
  totalSeats: number;
}

export interface CutoffData {
  collegeCode: string;
  branchCode: string;
  community: Community;
  seasonYear: number;
  roundNumber: number;
  closingRank: number;
}

export interface RankLookup {
  mathsMark: number;
  physicsMark: number;
  chemistryMark: number;
  rankMin: number | null;
  rankMax: number | null;
  sampleSize: number | null;
  confidence: "High" | "Medium" | "Low" | null;
  sourceYears: number[];
  isAbstain: boolean;
  disclaimer: string;
}

export interface Recommendation {
  collegeCode: string;
  collegeName: string;
  branchCode: string;
  branchName: string;
  district: string | null;
  cutoffRank: number | null;
  safety: SafetyLabel | null;
  seasonYear: number | null;
  isLocked: boolean;
}

export interface RecommendationsEnvelope {
  items: Recommendation[];
  total: number;
  returned: number;
  paid: boolean;
  restriction: "plan_limit" | "data_not_ready" | null;
}

export interface Choice {
  id: string;
  priority: number;
  collegeCode: string;
  collegeName: string | null;
  branchCode: string;
  branchName: string | null;
  district: string | null;
  systemCategory: SafetyLabel | null;
  manualCategory: SafetyLabel | null;
  notes: string | null;
}

export interface Subscription {
  id: string;
  workspaceId: string;
  status: "active" | "expired" | "none";
  activatedAt: string | null;
  expiresAt: string | null;
}

export interface ApiError {
  error: string;
  code: string;
}

export interface PaymentOrder {
  orderId: string;
  amountPaise: number;
  currency: string;
  keyId: string;
}

export interface AppConfig {
  tneaPhase: number;
  totalRounds: number;
  rankReleased: boolean;
  rollDataReady: boolean;
  freeChatLimit: number;
  seasonEndDate: string | null;
  broadcastActive: boolean;
  broadcastMessage: string | null;
  rankLookupReady: boolean;
  dataFreshness: Record<string, "missing" | "seeded_unverified" | "verified" | "stale" | "disabled">;
}
