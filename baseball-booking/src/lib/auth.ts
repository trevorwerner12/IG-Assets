import "server-only";
import { cache } from "react";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import type { Profile, UserRole } from "@/lib/types";

/**
 * The logged-in user's profile, or null for visitors. Wrapped in cache() so
 * calling it from several components in one request only hits the DB once.
 */
export const getCurrentProfile = cache(async (): Promise<Profile | null> => {
  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();
  const userId = data?.claims?.sub;
  if (!userId) return null;

  const { data: profile } = await supabase
    .from("profiles")
    .select("id, role, full_name, email, phone")
    .eq("id", userId)
    .single();
  return (profile as Profile | null) ?? null;
});

/** Use at the top of private pages/actions. Sends visitors to the login page. */
export async function requireProfile(roles?: UserRole[], next = "/") {
  const profile = await getCurrentProfile();
  if (!profile) redirect(`/login?next=${encodeURIComponent(next)}`);
  if (roles && !roles.includes(profile.role)) redirect("/");
  return profile;
}

/** Where to send someone right after they log in. */
export function homeFor(role: UserRole) {
  if (role === "admin") return "/admin/coaches";
  if (role === "coach") return "/coach";
  return "/coaches";
}
