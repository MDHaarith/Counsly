export type FitBand = "Safe" | "Moderate" | "Ambitious";

export interface CollegeSummary {
  code: string;
  name: string;
  district: string;
  type: "Government" | "Aided" | "Self-Finance";
  branchCode: string;
  branchName: string;
  cutoff: number;
  cutoffRank: number;
  seats: number;
  autonomous: boolean;
  nba: boolean;
  hostel: boolean;
  transport: boolean;
  fees: number;
  placementRate: number;
  averagePackage: number;
  railway: string;
  distanceKm: number;
  fitScore: number;
  fitBand: FitBand;
}

export interface ChoiceDraft extends CollegeSummary {
  priority: number;
  notes: string;
}

export const districts = ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli"];
export const branches = [
  { code: "CS", name: "Computer Science and Engineering" },
  { code: "IT", name: "Information Technology" },
  { code: "EC", name: "Electronics and Communication Engineering" },
  { code: "ME", name: "Mechanical Engineering" },
];

export const collegeCatalog: CollegeSummary[] = [
  {
    code: "0001",
    name: "College of Engineering, Guindy",
    district: "Chennai",
    type: "Government",
    branchCode: "CS",
    branchName: "Computer Science and Engineering",
    cutoff: 198.5,
    cutoffRank: 410,
    seats: 120,
    autonomous: true,
    nba: true,
    hostel: true,
    transport: true,
    fees: 25000,
    placementRate: 98,
    averagePackage: 8.5,
    railway: "Chennai Central",
    distanceKm: 8.1,
    fitScore: 88,
    fitBand: "Ambitious",
  },
  {
    code: "2006",
    name: "PSG College of Technology",
    district: "Coimbatore",
    type: "Aided",
    branchCode: "IT",
    branchName: "Information Technology",
    cutoff: 195,
    cutoffRank: 3120,
    seats: 120,
    autonomous: true,
    nba: true,
    hostel: true,
    transport: true,
    fees: 85000,
    placementRate: 96,
    averagePackage: 7.8,
    railway: "Coimbatore Junction",
    distanceKm: 5.4,
    fitScore: 95,
    fitBand: "Safe",
  },
  {
    code: "0004",
    name: "Madras Institute of Technology",
    district: "Chennai",
    type: "Government",
    branchCode: "EC",
    branchName: "Electronics and Communication Engineering",
    cutoff: 196,
    cutoffRank: 2180,
    seats: 90,
    autonomous: true,
    nba: true,
    hostel: true,
    transport: false,
    fees: 30000,
    placementRate: 95,
    averagePackage: 7.2,
    railway: "Tambaram",
    distanceKm: 4.2,
    fitScore: 91,
    fitBand: "Moderate",
  },
  {
    code: "1315",
    name: "Sri Sivasubramaniya Nadar College of Engineering",
    district: "Chennai",
    type: "Self-Finance",
    branchCode: "CS",
    branchName: "Computer Science and Engineering",
    cutoff: 194.2,
    cutoffRank: 4290,
    seats: 180,
    autonomous: true,
    nba: true,
    hostel: true,
    transport: true,
    fees: 95000,
    placementRate: 94,
    averagePackage: 7.4,
    railway: "Chengalpattu",
    distanceKm: 22.7,
    fitScore: 89,
    fitBand: "Safe",
  },
  {
    code: "2718",
    name: "Thiagarajar College of Engineering",
    district: "Madurai",
    type: "Aided",
    branchCode: "ME",
    branchName: "Mechanical Engineering",
    cutoff: 188.4,
    cutoffRank: 12110,
    seats: 120,
    autonomous: true,
    nba: true,
    hostel: true,
    transport: true,
    fees: 65000,
    placementRate: 87,
    averagePackage: 5.8,
    railway: "Madurai Junction",
    distanceKm: 7.3,
    fitScore: 82,
    fitBand: "Safe",
  },
];

export const choiceDrafts: ChoiceDraft[] = collegeCatalog.slice(0, 4).map((college, index) => ({
  ...college,
  priority: index + 1,
  notes: [
    "Dream choice. Keep it first if the upward strategy stays aggressive.",
    "Strong safety anchor with high branch fit.",
    "Moderate target if ECE remains preferred over city.",
    "Good backup for CSE with solid hostel and transport support.",
  ][index],
}));

export const trendRows = [
  { year: "2023", safe: 173, moderate: 188, ambitious: 196 },
  { year: "2024", safe: 176, moderate: 190, ambitious: 197 },
  { year: "2025", safe: 179, moderate: 192, ambitious: 198 },
  { year: "2026", safe: 181, moderate: 193, ambitious: 198 },
];

export const confirmationOptions = [
  {
    title: "Accept and Join",
    consequence: "Report to the allotted college with the provisional allotment letter before reporting closes.",
    tfc: false,
  },
  {
    title: "Accept and Upward",
    consequence: "Keep the allotted seat while remaining eligible for a better higher-priority choice.",
    tfc: true,
  },
  {
    title: "Decline and Upward",
    consequence: "Release this seat and stay in upward movement only if the confirmation rule allows it.",
    tfc: true,
  },
  {
    title: "Decline and Quit",
    consequence: "Leave this counselling path for the current cycle. This cannot be treated as a pause.",
    tfc: false,
  },
];

export function getCollege(code: string) {
  return collegeCatalog.find((college) => college.code === code);
}

export function currency(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function toneForBand(band: FitBand) {
  if (band === "Safe") return "safe";
  if (band === "Moderate") return "warning";
  return "coral";
}
