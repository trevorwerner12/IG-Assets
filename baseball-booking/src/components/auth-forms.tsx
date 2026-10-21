"use client";

import Link from "next/link";
import { useActionState, useState } from "react";
import { logIn, signUp, type FormState } from "@/app/auth-actions";
import { useKeepForm } from "@/lib/use-keep-form";

function FormMessage({ state }: { state: FormState }) {
  if (state?.error)
    return (
      <p role="alert" className="rounded-xl bg-stitch/10 px-3 py-2 text-sm font-medium text-stitch-dark">
        {state.error}
      </p>
    );
  if (state?.message)
    return (
      <p role="status" className="rounded-xl bg-field-light px-3 py-2 text-sm font-medium text-field">
        {state.message}
      </p>
    );
  return null;
}

export function LoginForm({ next }: { next?: string }) {
  const [state, action, pending] = useActionState(logIn, undefined);
  const onSubmit = useKeepForm(action);
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <input type="hidden" name="next" value={next ?? ""} />
      <div>
        <label htmlFor="email" className="label">
          Email
        </label>
        <input id="email" name="email" type="email" autoComplete="email" required className="input" />
      </div>
      <div>
        <label htmlFor="password" className="label">
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          className="input"
        />
      </div>
      <FormMessage state={state} />
      <button className="btn-primary w-full" disabled={pending}>
        {pending ? "Logging in…" : "Log in"}
      </button>
      <p className="text-center text-sm text-muted">
        New here?{" "}
        <Link href={`/signup${next ? `?next=${encodeURIComponent(next)}` : ""}`} className="font-semibold text-stitch">
          Create an account
        </Link>
      </p>
    </form>
  );
}

export function SignupForm({
  defaultRole,
  next,
}: {
  defaultRole: "family" | "coach";
  next?: string;
}) {
  const [state, action, pending] = useActionState(signUp, undefined);
  const [role, setRole] = useState(defaultRole);
  const onSubmit = useKeepForm(action);

  if (state?.message) return <FormMessage state={state} />;

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <input type="hidden" name="next" value={next ?? ""} />
      <fieldset>
        <legend className="label">I am a…</legend>
        <div className="grid grid-cols-2 gap-2">
          {(
            [
              ["family", "Parent / Player"],
              ["coach", "Coach"],
            ] as const
          ).map(([value, label]) => (
            <label
              key={value}
              className={`flex min-h-11 cursor-pointer items-center justify-center rounded-xl border px-3 font-semibold transition ${
                role === value ? "border-navy bg-navy text-white" : "border-line bg-white text-navy"
              }`}
            >
              <input
                type="radio"
                name="role"
                value={value}
                checked={role === value}
                onChange={() => setRole(value)}
                className="sr-only"
              />
              {label}
            </label>
          ))}
        </div>
      </fieldset>
      <div>
        <label htmlFor="full_name" className="label">
          {role === "coach" ? "Your full name" : "Parent's full name"}
        </label>
        <input id="full_name" name="full_name" autoComplete="name" required className="input" />
      </div>
      <div>
        <label htmlFor="email" className="label">
          Email
        </label>
        <input id="email" name="email" type="email" autoComplete="email" required className="input" />
      </div>
      <div>
        <label htmlFor="password" className="label">
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="new-password"
          minLength={8}
          required
          className="input"
        />
        <p className="hint">At least 8 characters.</p>
      </div>
      <FormMessage state={state} />
      <button className="btn-primary w-full" disabled={pending}>
        {pending ? "Creating account…" : role === "coach" ? "Continue to application" : "Create account"}
      </button>
      <p className="text-center text-sm text-muted">
        Already have an account?{" "}
        <Link href="/login" className="font-semibold text-stitch">
          Log in
        </Link>
      </p>
    </form>
  );
}
