"use server";

import { revalidatePath } from "next/cache";
import { getCurrentProfile } from "@/lib/auth";
import {
  LESSON_LENGTHS,
  METRO_AREAS,
  SPECIALTIES,
  TIMEZONES,
  US_STATES,
} from "@/lib/constants";
import { slugify } from "@/lib/format";
import { createAdminClient } from "@/lib/supabase/admin";
import { createClient } from "@/lib/supabase/server";

export type CoachFormState = { error?: string; message?: string } | undefined;

const text = (formData: FormData, key: string, max = 200) =>
  String(formData.get(key) ?? "").trim().slice(0, max);

/**
 * Saves the coach application (first time) or profile edits (after that).
 * Everything is checked here on the server; never trust what the browser sends.
 */
export async function saveCoachProfile(
  _prev: CoachFormState,
  formData: FormData,
): Promise<CoachFormState> {
  const profile = await getCurrentProfile();
  if (!profile) return { error: "Please log in again." };

  // ---- Read and check the fields ----
  const displayName = text(formData, "display_name", 80);
  const specialties = formData
    .getAll("specialties")
    .map(String)
    .filter((s) => SPECIALTIES.some((x) => x.value === s));
  const price = Number(formData.get("lesson_price"));
  const length = Number(formData.get("lesson_length_minutes"));
  const state = text(formData, "state", 2);
  const metro = text(formData, "metro_area", 60);
  const timezone = text(formData, "timezone", 40);
  const zip = text(formData, "zip", 10);
  const city = text(formData, "city", 80);
  const discount5 = Number(formData.get("package_5_discount_pct") ?? 5);
  const discount10 = Number(formData.get("package_10_discount_pct") ?? 10);
  const photoUrl = text(formData, "photo_url", 500);

  if (!displayName) return { error: "Enter the name families will see." };
  if (specialties.length === 0) return { error: "Pick at least one specialty." };
  if (!(price >= 10 && price <= 1000)) return { error: "Lesson price must be between $10 and $1,000." };
  if (!LESSON_LENGTHS.includes(length as (typeof LESSON_LENGTHS)[number]))
    return { error: "Pick a lesson length." };
  if (!city) return { error: "Enter your city." };
  if (!US_STATES.some((s) => s.code === state)) return { error: "Pick your state." };
  if (!METRO_AREAS.includes(metro as (typeof METRO_AREAS)[number]))
    return { error: "Pick your metro area (or Other)." };
  if (!TIMEZONES.some((t) => t.value === timezone)) return { error: "Pick your time zone." };
  if (zip && !/^\d{5}$/.test(zip)) return { error: "ZIP code should be 5 digits." };
  for (const d of [discount5, discount10]) {
    if (!(Number.isInteger(d) && d >= 0 && d <= 50))
      return { error: "Package discounts must be whole numbers from 0 to 50." };
  }
  const photoPrefix = `${process.env.NEXT_PUBLIC_SUPABASE_URL}/storage/v1/object/public/coach-photos/${profile.id}/`;
  if (photoUrl && !photoUrl.startsWith(photoPrefix)) return { error: "Please re-upload your photo." };

  const publicFields = {
    display_name: displayName,
    photo_url: photoUrl || null,
    bio: text(formData, "bio", 2000),
    playing_background: text(formData, "playing_background", 1000),
    specialties,
    lesson_price_cents: Math.round(price * 100),
    lesson_length_minutes: length,
    location_name: text(formData, "location_name", 120),
    address: text(formData, "address", 200),
    city,
    state,
    zip: zip || null,
    metro_area: metro,
    timezone,
    package_5_discount_pct: discount5,
    package_10_discount_pct: discount10,
  };

  const supabase = await createClient();
  const { data: existing } = await supabase
    .from("coaches")
    .select("id")
    .eq("profile_id", profile.id)
    .maybeSingle();

  // ---- Editing an existing profile ----
  if (existing) {
    const { error } = await supabase.from("coaches").update(publicFields).eq("id", existing.id);
    if (error) return { error: "Couldn't save your profile. Please try again." };
    revalidatePath("/coach");
    return { message: "Profile saved." };
  }

  // ---- First-time application ----
  const yearsCoaching = Number(formData.get("years_coaching"));
  if (!text(formData, "references_text", 1000))
    return { error: "Please list at least one reference." };

  const admin = createAdminClient();
  const slug = await uniqueSlug(admin, displayName);

  const { data: coach, error: insertError } = await supabase
    .from("coaches")
    .insert({ ...publicFields, profile_id: profile.id, slug, status: "pending" })
    .select("id")
    .single();
  if (insertError || !coach) return { error: "Couldn't submit your application. Please try again." };

  const { error: privateError } = await supabase.from("coach_private").insert({
    coach_id: coach.id,
    years_coaching: Number.isFinite(yearsCoaching) && yearsCoaching >= 0 ? Math.round(yearsCoaching) : null,
    certifications: text(formData, "certifications", 1000) || null,
    references_text: text(formData, "references_text", 1000),
    why_join: text(formData, "why_join", 1000) || null,
  });
  if (privateError) return { error: "Saved your profile, but not your application details. Please contact us." };

  // Families who apply become coaches. Only trusted server code may change roles.
  if (profile.role === "family") {
    await admin.from("profiles").update({ role: "coach" }).eq("id", profile.id);
  }

  revalidatePath("/", "layout");
  return { message: "Application submitted! We'll review it and email you within a few days." };
}

async function uniqueSlug(admin: ReturnType<typeof createAdminClient>, name: string) {
  const base = slugify(name) || "coach";
  const { data } = await admin.from("coaches").select("slug").like("slug", `${base}%`);
  const taken = new Set((data ?? []).map((r) => r.slug as string));
  if (!taken.has(base)) return base;
  for (let i = 2; ; i++) if (!taken.has(`${base}-${i}`)) return `${base}-${i}`;
}
