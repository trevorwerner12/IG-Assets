import "server-only";
import { createClient } from "@supabase/supabase-js";

/**
 * Supabase client with full access that skips all security rules.
 * Server-only: use it just for trusted actions (e.g. promoting a user to
 * coach) after you've checked who is asking.
 */
export function createAdminClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SECRET_KEY!,
    { auth: { persistSession: false, autoRefreshToken: false } },
  );
}
