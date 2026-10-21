import Link from "next/link";
import { getCurrentProfile, homeFor } from "@/lib/auth";
import { Logo } from "./logo";

export async function Header() {
  const profile = await getCurrentProfile();

  return (
    <header className="sticky top-0 z-30 bg-navy text-white shadow-md">
      <div className="container-page flex h-14 items-center justify-between gap-2">
        <Logo />
        <nav className="flex items-center gap-1 whitespace-nowrap text-sm font-semibold sm:gap-2">
          <Link href="/coaches" className="rounded-lg px-2 py-2 hover:bg-white/10">
            <span className="sm:hidden">Coaches</span>
            <span className="hidden sm:inline">Find a coach</span>
          </Link>
          {profile ? (
            // A <details> dropdown works without any JavaScript.
            <details className="group relative">
              <summary className="flex cursor-pointer list-none items-center gap-1 rounded-lg px-2 py-2 hover:bg-white/10 [&::-webkit-details-marker]:hidden">
                Account
                <svg viewBox="0 0 20 20" aria-hidden="true" className="h-4 w-4 transition group-open:rotate-180">
                  <path d="M5 8l5 5 5-5" fill="none" stroke="currentColor" strokeWidth="2" />
                </svg>
              </summary>
              <div className="absolute right-0 mt-2 w-52 overflow-hidden rounded-xl bg-white text-ink shadow-lg ring-1 ring-line">
                <p className="truncate border-b border-line px-4 py-2 text-xs font-normal text-muted">
                  {profile.email}
                </p>
                {profile.role !== "family" && (
                  <Link href={homeFor(profile.role)} className="block px-4 py-3 hover:bg-chalk">
                    {profile.role === "admin" ? "Admin dashboard" : "Coach dashboard"}
                  </Link>
                )}
                <form action="/auth/signout" method="post">
                  <button className="block w-full px-4 py-3 text-left text-stitch hover:bg-chalk">
                    Sign out
                  </button>
                </form>
              </div>
            </details>
          ) : (
            <Link href="/login" className="rounded-lg bg-white px-3 py-2 text-navy hover:bg-chalk">
              Log in
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
