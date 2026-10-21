# Youth Baseball Lessons: Phoenix

A mobile-first booking marketplace for private youth baseball lessons.
Built with Next.js, TypeScript, Tailwind, Supabase, Stripe Connect, and Resend.

## Build status

- [x] **Step 0: Database schema** (`supabase/migrations/`), explained in [`docs/SCHEMA.md`](docs/SCHEMA.md)
- [ ] Phase 1: Coach profiles and browsing
- [ ] Phase 2: Booking and availability
- [ ] Phase 3: Payments (Stripe Connect, test mode)
- [ ] Phase 4: Packages, reviews, and admin dashboard

## Step 0: Put the schema into Supabase

1. Create a free account at https://supabase.com and click **New project**.
   - Name: anything, e.g. `baseball-lessons`
   - Region: **West US** (closest to Phoenix)
   - Save the database password somewhere safe.
2. Wait for the project to finish setting up (about 2 minutes).
3. In the left sidebar, open **SQL Editor** and click **New query**.
4. Open `supabase/migrations/20261021000000_initial_schema.sql` from this repo,
   copy the **whole file**, paste it into the editor, and click **Run**.
   You should see "Success. No rows returned."
5. Check that it worked: in **Table Editor** you should see `profiles`,
   `coaches`, `bookings`, and the other tables.

### Make yourself the admin (do this after Phase 1, once you can sign up)

Sign up in the app with your email, then run this in the Supabase SQL Editor
(swap in your own email):

```sql
update public.profiles set role = 'admin' where email = 'you@example.com';
```

## Where API keys will go (later phases)

You'll create a file named `.env.local` in this folder. It is never committed
to git. Each phase will tell you exactly which keys to paste in, and where to
find them.
