import Link from "next/link";

export default function AuthErrorPage() {
  return (
    <div className="container-page max-w-md py-10">
      <h1 className="heading text-3xl">That link didn&apos;t work</h1>
      <p className="mt-2 text-muted">
        It may have expired or already been used. Try logging in. If your email still isn&apos;t
        confirmed, sign up again to get a new link.
      </p>
      <Link href="/login" className="btn-primary mt-5">
        Go to login
      </Link>
    </div>
  );
}
