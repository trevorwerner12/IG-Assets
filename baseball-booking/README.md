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

### 1. Create the Supabase project

1. Go to https://supabase.com, sign in, and click **New project**.
   Name: `baseball-lessons`. Region: any US region. Save the database password.
2. When it's ready, open **SQL Editor → New query**.
3. Run each file in `supabase/migrations/` **in order**: copy the whole file,
   paste it, click **Run**, then do the next one:
   1. `20261021000000_initial_schema.sql`
   2. `20261022000000_nationwide_locations.sql`

   (If you already ran the first file earlier, just run the second one.)

### 2. Fix the confirmation email link (important on phones)

Parents often sign up on one app and tap the email link in another, which
breaks Supabase's default link. To fix it:

1. In Supabase, go to **Authentication → Emails → Templates → Confirm signup**.
2. Find the link in the message body (it contains `{{ .ConfirmationURL }}`) and
   replace that link's URL with:
   ```
   {{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=email&next=/coach
   ```
3. Go to **Authentication → URL Configuration**. Set **Site URL** to
   `http://localhost:3000` for now (you'll change it when the site goes live).

### 3. Add your API keys

1. In this folder, copy `.env.example` to a new file named `.env.local`.
   ```
   cp .env.example .env.local
   ```
2. In Supabase, go to **Project Settings → API Keys** and paste the values into `.env.local`:
   - **Project URL** → `NEXT_PUBLIC_SUPABASE_URL`
     (also shown under Project Settings → Data API)
   - **Publishable key** (`sb_publishable_...`) → `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
   - **Secret key** (`sb_secret_...`) → `SUPABASE_SECRET_KEY`

   ⚠️ The secret key bypasses all security rules. Never share it, post it, or commit it.
   `.env.local` is already ignored by git.

### 4. Install and run

In a terminal, in this `baseball-booking` folder:

```bash
npm install        # downloads the libraries (first time only, takes about a minute)
npm run seed       # optional: adds 8 sample coaches in Phoenix and Houston
npm run dev        # starts the site
```

Open http://localhost:3000. To try it on your phone, connect to the same
Wi-Fi and open `http://<your computer's IP>:3000`.

Sample logins created by `npm run seed` (password `Practice123!`):
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
