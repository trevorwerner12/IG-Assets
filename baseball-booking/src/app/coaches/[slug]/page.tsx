import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CoachAvatar } from "@/components/coach-avatar";
import { RatingLine, Stars } from "@/components/stars";
import { getCoachBySlug, getCoachReviews } from "@/lib/coaches";
import { specialtyLabel } from "@/lib/constants";
import { formatPrice, packagePriceCents } from "@/lib/format";

export async function generateMetadata({
  params,
}: PageProps<"/coaches/[slug]">): Promise<Metadata> {
  const coach = await getCoachBySlug((await params).slug);
  return { title: coach ? `${coach.display_name}, baseball coach` : "Coach not found" };
}

export default async function CoachProfilePage({ params }: PageProps<"/coaches/[slug]">) {
  const coach = await getCoachBySlug((await params).slug);
  if (!coach) notFound();
  const reviews = await getCoachReviews(coach.id);

  const place = [coach.city, coach.state].filter(Boolean).join(", ");
  const packages = [
    { count: 5, pct: coach.package_5_discount_pct },
    { count: 10, pct: coach.package_10_discount_pct },
  ];

  return (
    <div className="pb-28">
      {/* Header band */}
      <section className="bg-navy pb-6 pt-4 text-white">
        <div className="container-page">
          <Link href="/coaches" className="text-sm text-white/70 hover:text-white">
            ← All coaches
          </Link>
          {coach.status !== "approved" && (
            <p className="mt-3 rounded-lg bg-gold px-3 py-2 text-sm font-semibold text-navy">
              Preview: this profile isn&apos;t public yet (status: {coach.status}).
            </p>
          )}
          <div className="mt-4 flex items-center gap-4">
            <CoachAvatar
              name={coach.display_name}
              photoUrl={coach.photo_url}
              size={104}
              className="ring-4 ring-white/20"
            />
            <div className="min-w-0">
              <h1 className="font-display text-3xl font-bold uppercase leading-tight tracking-wide sm:text-4xl">
                {coach.display_name}
              </h1>
              <p className="text-white/80">{place}</p>
              <div className="mt-1 [&_*]:text-white">
                <RatingLine avg={coach.avg_rating} count={coach.review_count} />
              </div>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-1.5">
            {coach.specialties.map((s) => (
              <span
                key={s}
                className="rounded-full bg-white/10 px-2.5 py-0.5 text-xs font-semibold"
              >
                {specialtyLabel(s)}
              </span>
            ))}
          </div>
        </div>
      </section>

      <div className="container-page mt-5 grid gap-4 md:grid-cols-3">
        <div className="space-y-4 md:col-span-2">
          {coach.bio && (
            <section className="card p-5">
              <h2 className="heading text-xl">About</h2>
              <p className="mt-2 whitespace-pre-line text-ink/90">{coach.bio}</p>
            </section>
          )}
          {coach.playing_background && (
            <section className="card p-5">
              <h2 className="heading text-xl">Playing background</h2>
              <p className="mt-2 whitespace-pre-line text-ink/90">{coach.playing_background}</p>
            </section>
          )}
          <section className="card p-5">
            <h2 className="heading text-xl">Reviews</h2>
            {reviews.length === 0 ? (
              <p className="mt-2 text-muted">No reviews yet. Be one of the first families!</p>
            ) : (
              <ul className="mt-3 divide-y divide-line">
                {reviews.map((r) => (
                  <li key={r.id} className="py-3">
                    <div className="flex items-center justify-between">
                      <Stars rating={r.rating} />
                      <time className="text-xs text-muted" dateTime={r.created_at}>
                        {new Date(r.created_at).toLocaleDateString("en-US", {
                          month: "short",
                          year: "numeric",
                        })}
                      </time>
                    </div>
                    {r.comment && <p className="mt-1 text-ink/90">{r.comment}</p>}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>

        <aside className="space-y-4">
          <section className="card p-5">
            <p className="text-3xl font-bold text-navy">
              {formatPrice(coach.lesson_price_cents)}
              <span className="text-base font-medium text-muted">
                {" "}
                / {coach.lesson_length_minutes} min lesson
              </span>
            </p>
            <h3 className="mt-4 text-sm font-semibold uppercase tracking-wide text-muted">
              Lesson packages
            </h3>
            <ul className="mt-2 space-y-2">
              {packages.map((p) => (
                <li
                  key={p.count}
                  className="flex items-center justify-between rounded-xl bg-chalk px-3 py-2"
                >
                  <span className="font-semibold">{p.count} lessons</span>
                  <span>
                    {formatPrice(packagePriceCents(coach.lesson_price_cents, p.count, p.pct))}
                    {p.pct > 0 && (
                      <span className="ml-1 text-xs font-semibold text-field">save {p.pct}%</span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </section>
          <section className="card p-5">
            <h2 className="heading text-xl">Where</h2>
            <p className="mt-2 font-semibold">{coach.location_name || "Location shared after booking"}</p>
            <p className="text-muted">{place}</p>
            <p className="hint">The exact address is sent with your booking confirmation.</p>
          </section>
          <section className="card flex items-start gap-3 p-5">
            <span className="mt-0.5 text-field" aria-hidden="true">
              ✔
            </span>
            <p className="text-sm text-ink/80">
              <strong className="text-navy">Vetted coach.</strong> Approved by our team and
              background checked.
            </p>
          </section>
        </aside>
      </div>

      {/* Sticky booking bar (booking opens in Phase 2) */}
      <div className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-white/95 backdrop-blur">
        <div className="container-page flex items-center justify-between gap-3 py-3">
          <div>
            <p className="font-bold text-navy">{formatPrice(coach.lesson_price_cents)}</p>
            <p className="text-xs text-muted">{coach.lesson_length_minutes} min · {place}</p>
          </div>
          <button className="btn-primary" disabled>
            Booking opens soon
          </button>
        </div>
      </div>
    </div>
  );
}

