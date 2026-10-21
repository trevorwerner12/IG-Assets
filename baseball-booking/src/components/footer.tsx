import Link from "next/link";
import { SITE_NAME } from "@/lib/site";

export function Footer() {
  return (
    <footer className="mt-16 border-t border-line bg-white">
      <div className="container-page flex flex-col gap-4 py-8 text-sm text-muted sm:flex-row sm:items-center sm:justify-between">
        <p>
          © {new Date().getFullYear()} {SITE_NAME}. Every coach is reviewed and background
          checked before their profile goes live.
        </p>
        <div className="flex gap-4 font-semibold text-navy">
          <Link href="/coaches">Find a coach</Link>
          <Link href="/coach">Coach with us</Link>
        </div>
      </div>
    </footer>
  );
}
