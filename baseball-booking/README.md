# Dugout Lessons: youth baseball lesson booking

A mobile-first marketplace where families book private baseball lessons with
vetted coaches anywhere in the US, starting with Phoenix and Houston.
Built with Next.js, TypeScript, Tailwind, Supabase, Stripe Connect, and Resend.

> The name "Dugout Lessons" is a placeholder. Change it in `src/lib/site.ts`.

## Build status

- [x] **Step 0: Database schema** (`supabase/migrations/`), explained in [`docs/SCHEMA.md`](docs/SCHEMA.md)
- [x] **Phase 1: Coach profiles and browsing.** Sign up and log in, coach application, browse and filter coaches, coach profile pages, basic admin approval
- [ ] Phase 2: Booking and availability
- [ ] Phase 3: Payments (Stripe Connect, test mode)
- [ ] Phase 4: Packages, reviews, and full admin dashboard

---

## One-time setup

You need **Node.js 20 or newer** installed (https://nodejs.org, the LTS version).
To check, run `node -v` in a terminal.

### 1. Supabase project ✅ (already done)

The Supabase project **baseball-lessons** is set up
(dashboard: https://supabase.com/dashboard/project/qdshsjnmuwwprftfukps):
- Both database files in `supabase/migrations/` have been run.
- Site URL is `http://localhost:3000` and redirects to it are allowed.
- 8 sample coaches (Phoenix and Houston), a demo family, and 15 reviews are loaded.

If you ever start a fresh project, run each file in `supabase/migrations/` in
order in the **SQL Editor**, then follow step 2.

### 2. Update the confirmation email (one-time, about a minute)

Parents often sign up in one app and tap the email link in another, which
breaks Supabase's default link. To fix it:

1. Open **Authentication → Emails → Templates → Confirm signup**.
2. Change **Subject** to `Confirm your Dugout Lessons account`.
3. Replace the **Message body** with:
   ```html
   <h2>Welcome to Dugout Lessons!</h2>
   <p>Tap the link below to confirm your email and finish creating your account.</p>
   <p><a href="{{ .RedirectTo }}&token_hash={{ .TokenHash }}&type=email">Confirm my email</a></p>
   <p>If you didn't sign up, you can ignore this email.</p>
   ```
4. Click **Save**.

> Supabase's built-in email sender only allows a few emails per hour, which is
> fine for testing. Before launch, we'll connect Resend so every email goes out.

### 3. Add your secret key

1. In this folder, copy `.env.example` to a new file named `.env.local`:
   ```
   cp .env.example .env.local
   ```
   The project URL and publishable key are already filled in.
2. In Supabase, go to **Project Settings → API Keys**. Under **Secret keys**,
   click the copy icon next to the `default` key. Paste it after
   `SUPABASE_SECRET_KEY=` in `.env.local`.

   ⚠️ The secret key bypasses all security rules. Never share it, post it, or commit it.
   `.env.local` is already ignored by git.

### 4. Install and run

In a terminal, in this `baseball-booking` folder:

```bash
npm install        # downloads the libraries (first time only, takes about a minute)
npm run dev        # starts the site
```

Open http://localhost:3000. To try it on your phone, connect to the same
Wi-Fi and open `http://<your computer's IP>:3000`.

Sample logins (password `Practice123!`):
- `demo-family@example.com` (a parent)
- `coach.marcus@example.com`, `coach.jamal@example.com`, and so on (coaches)

### 5. Make yourself the admin

1. Sign up on the site with your own email (choose "Parent / Player").
2. In the Supabase **SQL Editor**, run (with your email):
   ```sql
   update public.profiles set role = 'admin' where email = 'you@example.com';
   ```
3. Log in again. **Account → Admin dashboard** now shows coach applications.

---

## What's in Phase 1

| Page | Who | What it does |
|---|---|---|
| `/` | Everyone | Home page with search by area and specialty, top coaches, how it works |
| `/coaches` | Everyone | Browse coaches. Filter by area, specialty, city/ZIP, and max price; sort by rating or price |
| `/coaches/[name]` | Everyone | Coach profile: photo, bio, background, price, packages, location, reviews |
| `/signup`, `/login` | Everyone | Email and password accounts for parents and coaches |
| `/coach` | Coaches | Apply to coach, then edit your profile and see your approval status |
| `/admin/coaches` | Admin | Review applications, track background checks, approve, reject, or suspend |

How a coach goes live:
1. The coach signs up and fills out the application.
2. You mark their background check **Passed** on the admin page.
3. You click **Approve**. Approve stays locked until the check has passed.
4. Their profile appears in search.

## Adding a new city or market

Coaches can sign up from any US state, and their time zone is set
automatically. Families search by **metro area**. To add a new market (say
"Nashville"), add it to the `METRO_AREAS` list in `src/lib/constants.ts`.

## Before launch: remove the sample data

Run this in the Supabase **SQL Editor** to delete the sample coaches, demo
family, and their reviews (it only touches `@example.com` accounts):

```sql
begin;
create temp table sample_users on commit drop as
  select id from auth.users where email like '%@example.com';
delete from public.reviews  where family_id in (select id from sample_users);
delete from public.bookings where family_id in (select id from sample_users);
delete from public.coaches  where profile_id in (select id from sample_users);
delete from auth.users      where id in (select id from sample_users);
commit;
```

## Useful commands

| Command | What it does |
|---|---|
| `npm run dev` | Run the site locally with live reload |
| `npm run lint` | Check the code for common mistakes |
| `npm run typecheck` | Check that the TypeScript types line up |
| `npm run build` | Build the production version (what the live site will run) |
| `npm run seed` | Add sample coaches and reviews |

## Project layout

```
src/
  app/                 pages (each folder = a URL)
    coaches/           browse + coach profiles
    coach/             coach application & dashboard (+ actions.ts = server code)
    admin/coaches/     admin approvals
    login/ signup/ auth/
  components/          reusable UI pieces (coach card, header, forms…)
  lib/
    supabase/          database connections (browser, server, admin)
    constants.ts       specialties, states, time zones, metro areas
    site.ts            app name and platform fee
  proxy.ts             runs before each request: keeps people logged in
supabase/migrations/   database schema
scripts/seed.ts        sample data
```
