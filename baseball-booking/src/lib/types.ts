import type { Specialty, Timezone } from "./constants";

export type UserRole = "family" | "coach" | "admin";
export type CoachStatus = "pending" | "approved" | "rejected" | "suspended";
export type BackgroundCheckStatus =
  | "not_started"
  | "submitted"
  | "in_review"
  | "passed"
  | "failed"
  | "expired";

export type Profile = {
  id: string;
  role: UserRole;
  full_name: string;
  email: string;
  phone: string | null;
};

export type Coach = {
  id: string;
  profile_id: string;
  status: CoachStatus;
  slug: string;
  display_name: string;
  photo_url: string | null;
  bio: string;
  playing_background: string;
  specialties: Specialty[];
  lesson_price_cents: number;
  lesson_length_minutes: number;
  location_name: string;
  address: string;
  city: string;
  state: string;
  zip: string | null;
  metro_area: string;
  timezone: Timezone;
  package_5_discount_pct: number;
  package_10_discount_pct: number;
  approved_at: string | null;
  created_at: string;
};

export type CoachPrivate = {
  coach_id: string;
  years_coaching: number | null;
  certifications: string | null;
  references_text: string | null;
  why_join: string | null;
  background_check_status: BackgroundCheckStatus;
  background_check_provider: string | null;
  background_check_completed_on: string | null;
  background_check_expires_on: string | null;
  stripe_account_id: string | null;
  stripe_onboarding_complete: boolean;
  rejection_reason: string | null;
  admin_notes: string | null;
};

export type RatingSummary = { avg_rating: number; review_count: number };

export type Review = {
  id: string;
  rating: number;
  comment: string | null;
  created_at: string;
};
