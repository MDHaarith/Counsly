// === Communities ===
export type Community = 'OC' | 'BC' | 'BCM' | 'MBC' | 'SC' | 'SCA' | 'ST';

// === Board ===
export type Board = 'State' | 'CBSE' | 'ICSE';

// === Safety Labels ===
export type SafetyLabel = 'safe' | 'moderate' | 'ambitious';

// === Student ===
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
  rankConfidence: 'High' | 'Medium' | 'Low' | null;
  onboardingComplete: boolean;
}

// === Onboarding ===
export type OnboardingStep = 'marks' | 'details' | 'rank';

export interface OnboardingState {
  currentStep: OnboardingStep;
  completed: boolean;
}

// === College ===
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

// === Branch ===
export interface Branch {
  code: string;
  name: string;
}

// === College Branch (with seat info) ===
export interface CollegeBranch {
  collegeCode: string;
  branchCode: string;
  totalSeats: number;
}

// === Cutoff ===
export interface CutoffData {
  collegeCode: string;
  branchCode: string;
  community: Community;
  seasonYear: number;
  roundNumber: number;
  closingRank: number;
}

// === Rank Lookup ===
export interface RankLookup {
  aggregateMark: number;
  rankMin: number;
  rankMax: number;
  sampleSize: number;
  confidence: 'High' | 'Medium' | 'Low';
  sourceYears: number[];
  isAbstain: boolean;
}

// === Recommendation ===
export interface Recommendation {
  collegeCode: string;
  collegeName: string;
  branchCode: string;
  branchName: string;
  district: string;
  closingRank: number;
  safety: SafetyLabel;
  seasonYear: number;
}

// === Choice ===
export interface Choice {
  id: string;
  priority: number;
  collegeCode: string;
  collegeName: string;
  branchCode: string;
  branchName: string;
  district: string;
  safety: SafetyLabel | null;
  notes: string | null;
  createdAt: string;
  updatedAt: string;
}

// === Subscription ===
export interface Subscription {
  id: string;
  workspaceId: string;
  status: 'active' | 'expired' | 'none';
  activatedAt: string | null;
  expiresAt: string | null;
}

// === TNEA Phase ===
export type TNEAPhase = 1 | 2 | 3 | 4 | 5;

// === Access Tier ===
export type AccessTier = 'free' | 'paid';

// === Restriction Reason ===
export type RestrictionReason = 'plan_limit' | 'tnea_phase' | 'data_not_ready';

// === API Error ===
export interface ApiError {
  error: string;
  code: string;
}

// === Payment ===
export interface PaymentOrder {
  orderId: string;
  amount: number;
  currency: string;
  status: 'created' | 'paid' | 'failed';
}

// === Phase Config ===
export interface AppConfig {
  tneaPhase: TNEAPhase;
  totalRounds: number;
  rankReleased: boolean;
  rollDataReady: boolean;
  freeChatLimit: number;
  seasonEndDate: string | null;
  broadcastActive: boolean;
  broadcastMessage: string | null;
  rankLookupReady: boolean;
}
