"use server";

import { redirect } from "next/navigation";
import { homeFor } from "@/lib/auth";
import { createClient } from "@/lib/supabase/server";
import type { UserRole } from "@/lib/types";

export type FormState = { error?: string; message?: string } | undefined;

/** Only allow redirects to pages on our own site (e.g. "/coach"). */
function safeNext(value: FormDataEntryValue | null) {
  const next = typeof value === "string" ? value : "";
  return next.startsWith("/") && !next.startsWith("//") ? next : null;
}

export async function logIn(_prev: FormState, formData: FormData): Promise<FormState> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  if (!email || !password) return { error: "Enter your email and password." };

  const supabase = await createClient();
  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) {
    return {
      error:
        error.code === "email_not_confirmed"
          ? "Please confirm your email first. Check your inbox for the link."
          : "That email and password don't match.",
    };
  }

  const { data: profile } = await supabase
    .from("profiles")
    .select("role")
    .eq("id", data.user.id)
    .single();
  redirect(safeNext(formData.get("next")) ?? homeFor((profile?.role as UserRole) ?? "family"));
}

export async function signUp(_prev: FormState, formData: FormData): Promise<FormState> {
  const fullName = String(formData.get("full_name") ?? "").trim();
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  const role = formData.get("role") === "coach" ? "coach" : "family";

  if (!fullName) return { error: "Enter your name." };
  if (!email) return { error: "Enter your email." };
  if (password.length < 8) return { error: "Use a password with at least 8 characters." };

  const next = role === "coach" ? "/coach" : safeNext(formData.get("next")) ?? "/coaches";
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

  const supabase = await createClient();
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: { full_name: fullName, role },
      emailRedirectTo: `${siteUrl}/auth/confirm?next=${encodeURIComponent(next)}`,
    },
  });
  if (error) {
    return {
      error:
        error.code === "user_already_exists"
          ? "An account with that email already exists. Try logging in."
          : error.message,
    };
  }

  // If email confirmation is turned off in Supabase, they're logged in now.
  if (data.session) redirect(next);

  return {
    message: `Almost done! We sent a confirmation link to ${email}. Tap it to finish signing up.`,
  };
}
