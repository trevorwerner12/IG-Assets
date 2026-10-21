import type { Metadata } from "next";
import Link from "next/link";
import { CoachProfileForm } from "@/components/coach-profile-form";
import { requireProfile } from "@/lib/auth";
import { createClient } from "@/lib/supabase/server";
import type { Coach, CoachPrivate } from "@/lib/types";

export const metadata: Metadata = { title: "Coach dashboard" };

export default async function CoachDashboardPage() {
  const profile = await requireProfile(undefined, "/coach");
  const supabase = await createClient();

  const { data: coachRow } = await supabase
    .from("coaches")
    .select("*")
    .eq("profile_id", profile.id)
    .maybeSingle();
  const coach = coachRow as Coach | null;

  const { data: privateRow } = coach
    ? await supabase
        .from("coach_private")
        .select("background_check_status, rejection_reason")
        .eq("coach_id", coach.id)
        .maybeSingle()
    : { data: null };
  const details = privateRow as Pick<CoachPrivate, "background_check_status" | "rejection_reason"> | null;

  return (
    <div className="container-page max-w-3xl py-6">
      <h1 className="heading text-3xl">{coach ? "Your coach profile" : "Apply to coach"}</h1>
      {!coach && (
        <p className="mt-1 text-muted">
          Tell us about yourself. Once we approve your application and your background check
          clears, your profile goes live and families can book you.
        </p>
      )}

      {coach && (
        <div className="mt-4">
          <StatusBanner status={coach.status} rejectionReason={details?.rejection_reason ?? null} />
          <div className="mt-3 flex flex-wrap gap-2 text-sm">
            <Link href={`/coaches/${coach.slug}`} className="btn-outline">
              {coach.status === "approved" ? "View my public profile" : "Preview my profile"}
            </Link>
          </div>
        </div>
      )}

      <div className="mt-5">
        <CoachProfileForm userId={profile.id} defaultName={profile.full_name} coach={coach} />
      </div>
    </div>
  );
}

function StatusBanner({
  status,
  rejectionReason,
}: {
  status: Coach["status"];
  rejectionReason: string | null;
}) {
  const styles = {
    pending: ["bg-gold/20 text-navy", "Application under review", "We'll email you once you're approved. You can keep improving your profile while you wait."],
    approved: ["bg-field-light text-field", "You're live!", "Families can find your profile. Booking and availability settings are coming next."],
    rejected: ["bg-stitch/10 text-stitch-dark", "Application not approved", rejectionReason ?? "Reach out to us if you have questions."],
    suspended: ["bg-stitch/10 text-stitch-dark", "Profile paused", "Your profile is hidden from families. Contact us for details."],
  } as const;
  const [className, title, body] = styles[status];
  return (
    <div className={`rounded-2xl px-4 py-3 ${className}`}>
      <p className="font-bold">{title}</p>
      <p className="text-sm">{body}</p>
    </div>
  );
}
