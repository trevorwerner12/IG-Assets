import "server-only";
import { createClient } from "@/lib/supabase/server";
import { SPECIALTIES, type Specialty } from "@/lib/constants";
import type { Coach, RatingSummary, Review } from "@/lib/types";

export type CoachWithRating = Coach & RatingSummary;

export type CoachFilters = {
  specialty?: string;
  metro?: string;
  state?: string;
  q?: string; // city or ZIP
  maxPrice?: string; // dollars
  sort?: string; // "top" | "price_low" | "price_high"
};

/** Read filter values out of the page URL, e.g. /coaches?specialty=pitching */
export function parseFilters(params: Record<string, string | string[] | undefined>) {
  const get = (key: string) => {
    const value = params[key];
    return (Array.isArray(value) ? value[0] : value)?.trim() || undefined;
  };
  return {
    specialty: get("specialty"),
    metro: get("metro"),
    state: get("state"),
    q: get("q"),
    maxPrice: get("maxPrice"),
    sort: get("sort"),
  } satisfies CoachFilters;
}

const CARD_COLUMNS =
  "id, profile_id, status, slug, display_name, photo_url, bio, playing_background, specialties, lesson_price_cents, lesson_length_minutes, location_name, city, state, metro_area, timezone, package_5_discount_pct, package_10_discount_pct, approved_at, created_at";

/** Approved coaches matching the filters, with their average rating. */
export async function listCoaches(filters: CoachFilters = {}, limit = 60) {
  const supabase = await createClient();
  let query = supabase.from("coaches").select(CARD_COLUMNS).eq("status", "approved").limit(limit);

  if (filters.specialty && SPECIALTIES.some((s) => s.value === filters.specialty)) {
    query = query.contains("specialties", [filters.specialty as Specialty]);
  }
  if (filters.metro) query = query.eq("metro_area", filters.metro);
  if (filters.state) query = query.eq("state", filters.state);
  const maxPrice = Number(filters.maxPrice);
  if (maxPrice > 0) query = query.lte("lesson_price_cents", Math.round(maxPrice * 100));
  if (filters.q) {
    // Keep only safe characters before building the search filter.
    const q = filters.q.replace(/[^a-zA-Z0-9 .'-]/g, "").slice(0, 40);
    if (q) query = query.or(`city.ilike.%${q}%,zip.ilike.${q}%,metro_area.ilike.%${q}%`);
  }

  const { data, error } = await query;
  if (error) throw error;
  const coaches = await withRatings((data ?? []) as Coach[]);

  if (filters.sort === "price_low") {
    coaches.sort((a, b) => a.lesson_price_cents - b.lesson_price_cents);
  } else if (filters.sort === "price_high") {
    coaches.sort((a, b) => b.lesson_price_cents - a.lesson_price_cents);
  } else {
    // "Top rated": best average first, then most reviews, then newest.
    coaches.sort(
      (a, b) =>
        b.avg_rating - a.avg_rating ||
        b.review_count - a.review_count ||
        b.created_at.localeCompare(a.created_at),
    );
  }
  return coaches;
}

async function withRatings(coaches: Coach[]): Promise<CoachWithRating[]> {
  if (coaches.length === 0) return [];
  const supabase = await createClient();
  const { data } = await supabase
    .from("coach_rating_summary")
    .select("coach_id, avg_rating, review_count")
    .in(
      "coach_id",
      coaches.map((c) => c.id),
    );
  const byId = new Map(
    (data ?? []).map((r) => [r.coach_id as string, r as unknown as RatingSummary]),
  );
  return coaches.map((c) => ({
    ...c,
    avg_rating: Number(byId.get(c.id)?.avg_rating ?? 0),
    review_count: byId.get(c.id)?.review_count ?? 0,
  }));
}

/** One coach's public profile (null if missing or not approved). */
export async function getCoachBySlug(slug: string) {
  const supabase = await createClient();
  const { data } = await supabase
    .from("coaches")
    .select(CARD_COLUMNS)
    .eq("slug", slug)
    .maybeSingle();
  if (!data) return null;
  const [coach] = await withRatings([data as Coach]);
  return coach;
}

export async function getCoachReviews(coachId: string, limit = 20) {
  const supabase = await createClient();
  const { data } = await supabase
    .from("reviews")
    .select("id, rating, comment, created_at")
    .eq("coach_id", coachId)
    .eq("is_hidden", false)
    .order("created_at", { ascending: false })
    .limit(limit);
  return (data ?? []) as Review[];
}

/** Metro areas that currently have at least one approved coach. */
export async function getActiveMetroAreas() {
  const supabase = await createClient();
  const { data } = await supabase
    .from("coaches")
    .select("metro_area, state")
    .eq("status", "approved")
    .neq("metro_area", "");
  const counts = new Map<string, number>();
  for (const row of data ?? []) {
    counts.set(row.metro_area, (counts.get(row.metro_area) ?? 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([name, count]) => ({ name, count }));
}
