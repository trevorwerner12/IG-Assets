"use server";

import { revalidatePath } from "next/cache";
import { requireProfile } from "@/lib/auth";
import { createClient } from "@/lib/supabase/server";
import type { BackgroundCheckStatus, CoachStatus } from "@/lib/types";

const STATUSES: CoachStatus[] = ["pending", "approved", "rejected", "suspended"];
const CHECKS: BackgroundCheckStatus[] = ["not_started", "submitted", "in_review", "passed", "failed", "expired"];

export async function setCoachStatus(formData: FormData) {
  await requireProfile(["admin"]);
  const coachId = String(formData.get("coach_id"));
  const status = String(formData.get("status")) as CoachStatus;
  if (!STATUSES.includes(status)) return;

  const supabase = await createClient();

  if (status === "approved") {
    // Families are told every coach is background checked, so enforce it.
    const { data } = await supabase
      .from("coach_private")
      .select("background_check_status")
      .eq("coach_id", coachId)
      .single();
    if (data?.background_check_status !== "passed") {
      throw new Error("Mark the background check as passed before approving this coach.");
    }
  }

  await supabase
    .from("coaches")
    .update({ status, approved_at: status === "approved" ? new Date().toISOString() : null })
    .eq("id", coachId);

  if (status === "rejected") {
    await supabase
      .from("coach_private")
      .update({ rejection_reason: String(formData.get("rejection_reason") ?? "").trim() || null })
      .eq("coach_id", coachId);
  }
  revalidatePath("/", "layout");
}

export async function saveBackgroundCheck(formData: FormData) {
  await requireProfile(["admin"]);
  const status = String(formData.get("background_check_status")) as BackgroundCheckStatus;
  if (!CHECKS.includes(status)) return;
  const date = (key: string) => String(formData.get(key) ?? "") || null;

  const supabase = await createClient();
  await supabase
    .from("coach_private")
    .update({
      background_check_status: status,
      background_check_provider: String(formData.get("background_check_provider") ?? "").trim() || null,
      background_check_completed_on: date("background_check_completed_on"),
      background_check_expires_on: date("background_check_expires_on"),
      admin_notes: String(formData.get("admin_notes") ?? "").trim() || null,
    })
    .eq("coach_id", String(formData.get("coach_id")));
  revalidatePath("/admin/coaches");
}
