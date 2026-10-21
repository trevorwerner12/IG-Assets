import type { Metadata } from "next";
import { SignupForm } from "@/components/auth-forms";

export const metadata: Metadata = { title: "Create an account" };

export default async function SignupPage({ searchParams }: PageProps<"/signup">) {
  const { role, next } = await searchParams;
  return (
    <div className="container-page max-w-md py-10">
      <h1 className="heading text-3xl">Create your account</h1>
      <p className="mt-1 text-muted">Free to join. You only pay when you book a lesson.</p>
      <div className="card mt-5 p-5">
        <SignupForm
          defaultRole={role === "coach" ? "coach" : "family"}
          next={typeof next === "string" ? next : undefined}
        />
      </div>
    </div>
  );
}
