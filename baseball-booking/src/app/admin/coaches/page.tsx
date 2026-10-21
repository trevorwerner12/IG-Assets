import type { Metadata } from "next";
import Link from "next/link";
import { CoachAvatar } from "@/components/coach-avatar";
import { SpecialtyBadge } from "@/components/specialty-badge";
import { requireProfile } from "@/lib/auth";
import { formatPrice } from "@/lib/format";
import { createClient } from "@/lib/supabase/server";
import type { Coach, CoachPrivate, CoachStatus, Profile } from "@/lib/types";
import { saveBackgroundCheck, setCoachStatus } from "./actions";

export const metadata: Metadata = { title: "Admin: coaches" };

type Row = Coach & {
  profiles: Pick<Profile, "email" | "phone" | "full_name"> | null;
  coach_private: CoachPrivate | null;
};

const TABS: { value: CoachStatus; label: string }[] = [
  { value: "pending", label: "Pending" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "suspended", label: "Suspended" },
];

const CHECK_OPTIONS = [
  ["not_started", "Not started"],
  ["submitted", "Submitted"],
  ["in_review", "In review"],
  ["passed", "Passed"],
  ["failed", "Failed"],
  ["expired", "Expired"],
] as const;

export default async function AdminCoachesPage({ searchParams }: PageProps<"/admin/coaches">) {
  await requireProfile(["admin"], "/admin/coaches");
  const { status: statusParam } = await searchParams;
  const status = (TABS.find((t) => t.value === statusParam)?.value ?? "pending") as CoachStatus;

  const supabase = await createClient();
  const { data } = await supabase
    .from("coaches")
    .select("*, profiles(email, phone, full_name), coach_private(*)")
    .eq("status", status)
    .order("created_at", { ascending: false });
  const coaches = (data ?? []) as Row[];

  return (
    <div className="container-page py-6">
      <h1 className="heading text-3xl">Coaches</h1>
      <nav className="mt-4 flex gap-2 overflow-x-auto" aria-label="Coach status">
        {TABS.map((t) => (
          <Link
            key={t.value}
            href={`/admin/coaches?status=${t.value}`}
            className={`rounded-full px-4 py-2 text-sm font-semibold ${
              t.value === status ? "bg-navy text-white" : "bg-white text-navy ring-1 ring-line"
            }`}
          >
            {t.label}
          </Link>
        ))}
      </nav>

      {coaches.length === 0 && (
        <p className="card mt-4 p-6 text-center text-muted">No {status} coaches.</p>
      )}

      <ul className="mt-4 space-y-4">
        {coaches.map((c) => {
          const p = c.coach_private;
          return (
            <li key={c.id} className="card p-5">
              <div className="flex gap-4">
                <CoachAvatar name={c.display_name} photoUrl={c.photo_url} size={64} />
                <div className="min-w-0 flex-1">
                  <Link href={`/coaches/${c.slug}`} className="text-lg font-bold text-navy hover:underline">
                    {c.display_name}
                  </Link>
                  <p className="text-sm text-muted">
                    {c.profiles?.email}
                    {c.profiles?.phone && ` · ${c.profiles.phone}`}
                  </p>
                  <p className="text-sm text-muted">
                    {c.city}, {c.state} ({c.metro_area}) · {formatPrice(c.lesson_price_cents)} /{" "}
                    {c.lesson_length_minutes} min
                  </p>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {c.specialties.map((s) => (
                      <SpecialtyBadge key={s} value={s} />
                    ))}
                  </div>
                </div>
              </div>

              {p && (
                <dl className="mt-4 grid gap-2 rounded-xl bg-chalk p-3 text-sm sm:grid-cols-2">
                  <Detail label="Years coaching" value={p.years_coaching?.toString()} />
                  <Detail label="Certifications" value={p.certifications} />
                  <Detail label="References" value={p.references_text} />
                  <Detail label="Why join" value={p.why_join} />
                </dl>
              )}

              {p && (
                <form action={saveBackgroundCheck} className="mt-4 grid gap-3 sm:grid-cols-2">
                  <input type="hidden" name="coach_id" value={c.id} />
                  <div>
                    <label className="label" htmlFor={`bg-${c.id}`}>
                      Background check
                    </label>
                    <select
                      id={`bg-${c.id}`}
                      name="background_check_status"
                      defaultValue={p.background_check_status}
                      className="input"
                    >
                      {CHECK_OPTIONS.map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="label" htmlFor={`prov-${c.id}`}>
                      Provider
                    </label>
                    <input
                      id={`prov-${c.id}`}
                      name="background_check_provider"
                      defaultValue={p.background_check_provider ?? ""}
                      placeholder="e.g. Checkr, NCSI"
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="label" htmlFor={`done-${c.id}`}>
                      Completed on
                    </label>
                    <input
                      id={`done-${c.id}`}
                      type="date"
                      name="background_check_completed_on"
                      defaultValue={p.background_check_completed_on ?? ""}
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="label" htmlFor={`exp-${c.id}`}>
                      Expires on
                    </label>
                    <input
                      id={`exp-${c.id}`}
                      type="date"
                      name="background_check_expires_on"
                      defaultValue={p.background_check_expires_on ?? ""}
                      className="input"
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="label" htmlFor={`notes-${c.id}`}>
                      Admin notes (private)
                    </label>
                    <textarea
                      id={`notes-${c.id}`}
                      name="admin_notes"
                      rows={2}
                      defaultValue={p.admin_notes ?? ""}
                      className="input py-2"
                    />
                  </div>
                  <button className="btn-outline sm:col-span-2 sm:justify-self-start">
                    Save background check
                  </button>
                </form>
              )}

              <div className="mt-4 flex flex-wrap items-end gap-2 border-t border-line pt-4">
                {c.status !== "approved" && (
                  <form action={setCoachStatus}>
                    <input type="hidden" name="coach_id" value={c.id} />
                    <input type="hidden" name="status" value="approved" />
                    <button
                      className="btn bg-field text-white hover:opacity-90"
                      disabled={p?.background_check_status !== "passed"}
                      title={
                        p?.background_check_status !== "passed"
                          ? "Background check must be passed first"
                          : undefined
                      }
                    >
                      Approve
                    </button>
                  </form>
                )}
                {c.status === "pending" && (
                  <form action={setCoachStatus} className="flex flex-1 flex-wrap gap-2">
                    <input type="hidden" name="coach_id" value={c.id} />
                    <input type="hidden" name="status" value="rejected" />
                    <input
                      name="rejection_reason"
                      placeholder="Reason (shown to the coach)"
                      aria-label="Rejection reason"
                      className="input min-w-48 flex-1"
                    />
                    <button className="btn-outline text-stitch">Reject</button>
                  </form>
                )}
                {c.status === "approved" && (
                  <form action={setCoachStatus}>
                    <input type="hidden" name="coach_id" value={c.id} />
                    <input type="hidden" name="status" value="suspended" />
                    <button className="btn-outline text-stitch">Suspend</button>
                  </form>
                )}
              </div>
              {c.status === "pending" && p?.background_check_status !== "passed" && (
                <p className="hint">Approve unlocks once the background check is marked Passed.</p>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div>
      <dt className="font-semibold text-navy">{label}</dt>
      <dd className="whitespace-pre-line text-ink/80">{value || "N/A"}</dd>
    </div>
  );
}
