"use client";

export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <div className="container-page max-w-md py-16 text-center">
      <h1 className="heading text-3xl">Something went wrong</h1>
      <p className="mt-2 text-muted">Please try again. If it keeps happening, let us know.</p>
      <button onClick={reset} className="btn-primary mt-6">
        Try again
      </button>
    </div>
  );
}
