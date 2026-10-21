import type { Metadata } from "next";
import { Suspense } from "react";
import { CoachCard } from "@/components/coach-card";
import { CoachFiltersForm } from "@/components/coach-filters";
import { getActiveMetroAreas, listCoaches, parseFilters } from "@/lib/coaches";
import { specialtyLabel } from "@/lib/constants";

export const metadata: Metadata = { title: "Find a coach" };

export default async function CoachesPage({ searchParams }: PageProps<"/coaches">) {
  const params = await searchParams;
  // Changing filters shows the skeleton while new results load.
  return (
    <Suspense key={JSON.stringify(params)} fallback={<ResultsSkeleton />}>
      <CoachResults params={params} />
    </Suspense>
  );
}

async function CoachResults({ params }: { params: Record<string, string | string[] | undefined> }) {
  const filters = parseFilters(params);
  const [coaches, metros] = await Promise.all([listCoaches(filters), getActiveMetroAreas()]);

  const heading = [
    filters.specialty ? `${specialtyLabel(filters.specialty)} coaches` : "Baseball coaches",
    filters.metro ? `in the ${filters.metro} area` : null,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="container-page py-6">
      <h1 className="heading text-3xl">{heading}</h1>
      <p className="mt-1 text-muted">
        Every coach is reviewed and background checked before joining.
      </p>

      <div className="mt-5">
        <CoachFiltersForm filters={filters} metros={metros} />
      </div>

      <p className="mt-6 text-sm font-semibold text-muted">
        {coaches.length} {coaches.length === 1 ? "coach" : "coaches"} found
      </p>

      {coaches.length > 0 ? (
        <ul className="mt-3 grid gap-3 md:grid-cols-2">
          {coaches.map((coach) => (
            <li key={coach.id}>
              <CoachCard coach={coach} />
            </li>
          ))}
        </ul>
      ) : (
        <div className="card mt-3 p-8 text-center">
          <p className="font-semibold text-navy">No coaches match those filters yet.</p>
          <p className="mt-1 text-sm text-muted">
            Try a different area or specialty. We&apos;re adding coaches across the country.
          </p>
        </div>
      )}
    </div>
  );
}

function ResultsSkeleton() {
  return (
    <div className="container-page py-6" aria-busy="true" aria-label="Loading coaches">
      <div className="h-9 w-64 animate-pulse rounded-lg bg-line" />
      <div className="card mt-5 h-40 animate-pulse" />
      <div className="mt-9 grid gap-3 md:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="card h-36 animate-pulse" />
        ))}
      </div>
    </div>
  );
}
