import Link from "next/link";

export default function NotFound() {
  return (
    <div className="container-page max-w-md py-16 text-center">
      <p className="font-display text-6xl font-extrabold text-stitch">Foul ball</p>
      <p className="mt-2 text-muted">We couldn&apos;t find that page.</p>
      <Link href="/coaches" className="btn-primary mt-6">
        Find a coach
      </Link>
    </div>
  );
}
