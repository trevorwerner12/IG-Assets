import Link from "next/link";
import { CoachCard } from "@/components/coach-card";
import { BaseballIcon } from "@/components/logo";
import { getActiveMetroAreas, listCoaches } from "@/lib/coaches";
import { SPECIALTIES } from "@/lib/constants";

const SPECIALTY_BLURBS: Record<string, string> = {
  pitching: "Mechanics, command, velocity, and arm care.",
  hitting: "Swing path, timing, approach, and power.",
  catching: "Receiving, blocking, framing, and throws to second.",
  strength: "Speed, agility, and baseball-specific strength.",
};

export default async function HomePage() {
  const [featured, metros] = await Promise.all([
    listCoaches({ sort: "top" }, 4),
    getActiveMetroAreas(),
  ]);

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden bg-navy text-white">
        <div
          aria-hidden="true"
          className="absolute -right-24 -top-24 h-72 w-72 rounded-full border-[18px] border-dashed border-stitch/40"
        />
        <div className="container-page relative py-12 sm:py-20">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold">
            Youth baseball lessons
          </p>
          <h1 className="mt-3 max-w-2xl font-display text-5xl font-extrabold uppercase leading-[0.95] sm:text-6xl">
            Get better every rep with a coach you can trust
          </h1>
          <p className="mt-4 max-w-xl text-lg text-white/80">
            Book private pitching, hitting, catching, and strength lessons with vetted,
            background-checked coaches near you.
          </p>

          <form action="/coaches" className="mt-8 grid max-w-2xl gap-2 rounded-2xl bg-white p-2 sm:grid-cols-[1fr_1fr_auto]">
            <label className="sr-only" htmlFor="hero-metro">
              Area
            </label>
            <select id="hero-metro" name="metro" className="input border-0 text-ink" defaultValue="">
              <option value="">Any area</option>
              {metros.map((m) => (
                <option key={m.name} value={m.name}>
                  {m.name}
                </option>
              ))}
            </select>
            <label className="sr-only" htmlFor="hero-specialty">
              Specialty
            </label>
            <select
              id="hero-specialty"
              name="specialty"
              className="input border-0 text-ink"
              defaultValue=""
            >
              <option value="">Any specialty</option>
              {SPECIALTIES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
            <button className="btn-primary">Find a coach</button>
          </form>

          {metros.length > 0 && (
            <p className="mt-4 text-sm text-white/70">
              Now coaching in{" "}
              {metros.slice(0, 4).map((m, i) => (
                <span key={m.name}>
                  {i > 0 && ", "}
                  <Link
                    href={`/coaches?metro=${encodeURIComponent(m.name)}`}
                    className="font-semibold text-white underline-offset-2 hover:underline"
                  >
                    {m.name}
                  </Link>
                </span>
              ))}
              {metros.length > 4 && " and more"}
            </p>
          )}
        </div>
      </section>

      {/* Specialties */}
      <section className="container-page py-10">
        <h2 className="heading text-2xl">What do they want to work on?</h2>
        <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
          {SPECIALTIES.map((s) => (
            <Link
              key={s.value}
              href={`/coaches?specialty=${s.value}`}
              className="card group p-4 transition hover:border-stitch"
            >
              <BaseballIcon className="h-8 w-8 text-navy" />
              <h3 className="mt-3 font-display text-xl font-bold uppercase text-navy group-hover:text-stitch">
                {s.label}
              </h3>
              <p className="mt-1 text-sm text-muted">{SPECIALTY_BLURBS[s.value]}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Featured coaches */}
      {featured.length > 0 && (
        <section className="container-page pb-10">
          <div className="flex items-end justify-between">
            <h2 className="heading text-2xl">Top coaches</h2>
            <Link href="/coaches" className="text-sm font-semibold text-stitch">
              See all →
            </Link>
          </div>
          <ul className="mt-4 grid gap-3 md:grid-cols-2">
            {featured.map((coach) => (
              <li key={coach.id}>
                <CoachCard coach={coach} />
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* How it works */}
      <section className="bg-white py-10">
        <div className="container-page">
          <h2 className="heading text-2xl">How it works</h2>
          <ol className="mt-4 grid gap-4 md:grid-cols-3">
            {[
              ["Pick a coach", "Compare backgrounds, specialties, prices, and reviews from other families."],
              ["Book a time", "See open times and pay securely. Save with 5- and 10-lesson packages."],
              ["Track progress", "Get notes from your coach after every lesson."],
            ].map(([title, text], i) => (
              <li key={title} className="flex gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-stitch font-display text-lg font-bold text-white">
                  {i + 1}
                </span>
                <div>
                  <h3 className="font-bold text-navy">{title}</h3>
                  <p className="text-sm text-muted">{text}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Coach CTA */}
      <section className="container-page py-10">
        <div className="card flex flex-col items-start gap-4 bg-navy p-6 text-white sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="font-display text-2xl font-bold uppercase">Coach with us</h2>
            <p className="text-white/80">
              Set your own price and hours. We handle booking, payments, and reminders.
            </p>
          </div>
          <Link href="/signup?role=coach" className="btn-primary">
            Apply to coach
          </Link>
        </div>
      </section>
    </>
  );
}
