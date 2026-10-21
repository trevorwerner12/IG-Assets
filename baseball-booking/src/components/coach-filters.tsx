import Link from "next/link";
import { SPECIALTIES } from "@/lib/constants";
import type { CoachFilters } from "@/lib/coaches";

/**
 * A plain HTML form that reloads /coaches with the chosen filters in the URL.
 * Works on any phone, even before JavaScript loads, and the filtered URL can
 * be shared by text message.
 */
export function CoachFiltersForm({
  filters,
  metros,
}: {
  filters: CoachFilters;
  metros: { name: string; count: number }[];
}) {
  const activeCount = [filters.specialty, filters.metro, filters.q, filters.maxPrice].filter(
    Boolean,
  ).length;

  return (
    <form action="/coaches" className="card p-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="col-span-2 sm:col-span-1">
          <label htmlFor="metro" className="label">
            Area
          </label>
          <select id="metro" name="metro" defaultValue={filters.metro ?? ""} className="input">
            <option value="">All areas</option>
            {metros.map((m) => (
              <option key={m.name} value={m.name}>
                {m.name} ({m.count})
              </option>
            ))}
          </select>
        </div>
        <div className="col-span-2 sm:col-span-1">
          <label htmlFor="specialty" className="label">
            Specialty
          </label>
          <select
            id="specialty"
            name="specialty"
            defaultValue={filters.specialty ?? ""}
            className="input"
          >
            <option value="">All specialties</option>
            {SPECIALTIES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="q" className="label">
            City or ZIP
          </label>
          <input
            id="q"
            name="q"
            defaultValue={filters.q ?? ""}
            placeholder="e.g. Katy"
            className="input"
          />
        </div>
        <div>
          <label htmlFor="maxPrice" className="label">
            Max price
          </label>
          <select
            id="maxPrice"
            name="maxPrice"
            defaultValue={filters.maxPrice ?? ""}
            className="input"
          >
            <option value="">Any</option>
            {[50, 75, 100, 125, 150].map((p) => (
              <option key={p} value={p}>
                Up to ${p}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-3">
        <select
          name="sort"
          defaultValue={filters.sort ?? "top"}
          aria-label="Sort by"
          className="input w-auto flex-1 sm:flex-none"
        >
          <option value="top">Top rated</option>
          <option value="price_low">Price: low to high</option>
          <option value="price_high">Price: high to low</option>
        </select>
        <button className="btn-secondary flex-1 sm:flex-none">Show coaches</button>
        {activeCount > 0 && (
          <Link href="/coaches" className="text-sm font-semibold text-stitch">
            Clear
          </Link>
        )}
      </div>
    </form>
  );
}
