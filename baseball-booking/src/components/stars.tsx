export function Stars({ rating, className = "h-4 w-4" }: { rating: number; className?: string }) {
  return (
    <span className="inline-flex" aria-label={`${rating} out of 5 stars`} role="img">
      {[1, 2, 3, 4, 5].map((i) => {
        const fill = Math.max(0, Math.min(1, rating - (i - 1)));
        const id = `star-${i}-${Math.round(fill * 100)}`;
        return (
          <svg key={i} viewBox="0 0 20 20" className={className} aria-hidden="true">
            <defs>
              <linearGradient id={id}>
                <stop offset={fill} stopColor="#f2b01e" />
                <stop offset={fill} stopColor="#d9d6cc" />
              </linearGradient>
            </defs>
            <path
              fill={`url(#${id})`}
              d="M10 1.5l2.6 5.4 5.9.8-4.3 4.1 1 5.9L10 14.9l-5.2 2.8 1-5.9L1.5 7.7l5.9-.8z"
            />
          </svg>
        );
      })}
    </span>
  );
}

export function RatingLine({ avg, count }: { avg: number; count: number }) {
  if (count === 0) {
    return (
      <span className="rounded-full bg-field-light px-2 py-0.5 text-xs font-semibold text-field">
        New coach
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-sm">
      <Stars rating={avg} />
      <span className="font-semibold text-ink">{avg.toFixed(1)}</span>
      <span className="text-muted">({count})</span>
    </span>
  );
}
