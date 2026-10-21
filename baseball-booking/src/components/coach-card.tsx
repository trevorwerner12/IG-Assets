import Link from "next/link";
import type { CoachWithRating } from "@/lib/coaches";
import { formatPrice } from "@/lib/format";
import { CoachAvatar } from "./coach-avatar";
import { RatingLine } from "./stars";
import { SpecialtyBadge } from "./specialty-badge";

export function CoachCard({ coach }: { coach: CoachWithRating }) {
  return (
    <Link
      href={`/coaches/${coach.slug}`}
      className="card flex gap-4 p-4 transition hover:border-navy/40 hover:shadow-md"
    >
      <CoachAvatar name={coach.display_name} photoUrl={coach.photo_url} size={84} />
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <h3 className="truncate text-lg font-bold text-navy">{coach.display_name}</h3>
          <p className="shrink-0 text-right">
            <span className="text-lg font-bold text-ink">
              {formatPrice(coach.lesson_price_cents)}
            </span>
            <span className="block text-xs text-muted">{coach.lesson_length_minutes} min</span>
          </p>
        </div>
        <p className="truncate text-sm text-muted">
          {[coach.city, coach.state].filter(Boolean).join(", ")}
        </p>
        <div className="mt-1">
          <RatingLine avg={coach.avg_rating} count={coach.review_count} />
        </div>
        {coach.playing_background && (
          <p className="mt-2 line-clamp-2 text-sm text-ink/80">{coach.playing_background}</p>
        )}
        <div className="mt-2 flex flex-wrap gap-1.5">
          {coach.specialties.map((s) => (
            <SpecialtyBadge key={s} value={s} />
          ))}
        </div>
      </div>
    </Link>
  );
}
