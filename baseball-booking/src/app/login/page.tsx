import type { Metadata } from "next";
import { LoginForm } from "@/components/auth-forms";

export const metadata: Metadata = { title: "Log in" };

export default async function LoginPage({ searchParams }: PageProps<"/login">) {
  const { next } = await searchParams;
  return (
    <div className="container-page max-w-md py-10">
      <h1 className="heading text-3xl">Welcome back</h1>
      <div className="card mt-5 p-5">
        <LoginForm next={typeof next === "string" ? next : undefined} />
      </div>
    </div>
  );
}
