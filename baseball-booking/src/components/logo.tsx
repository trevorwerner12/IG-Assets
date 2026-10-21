import Link from "next/link";
import { SITE_NAME } from "@/lib/site";

export function BaseballIcon({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <circle cx="16" cy="16" r="14" fill="#fff" stroke="currentColor" strokeWidth="2" />
      <path
        d="M9 5.5c3 3 4.5 6.5 4.5 10.5S12 23.5 9 26.5M23 5.5c-3 3-4.5 6.5-4.5 10.5s1.5 7.5 4.5 10.5"
        fill="none"
        stroke="#c8102e"
        strokeWidth="1.8"
        strokeDasharray="2 2"
      />
    </svg>
  );
}

export function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2 text-white">
      <BaseballIcon />
      <span className="whitespace-nowrap font-display text-lg font-extrabold uppercase tracking-wide sm:text-xl">
        {SITE_NAME}
      </span>
    </Link>
  );
}
