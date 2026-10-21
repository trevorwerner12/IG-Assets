-- =============================================================================
-- Youth baseball coaching marketplace (Phoenix, AZ) — initial database schema
-- =============================================================================
-- Conventions used throughout:
--   * Money is stored as whole cents in integer columns (e.g. $65.00 = 6500).
--     This avoids rounding errors that happen with decimals/floats.
--   * Moments in time are `timestamptz`. Coach weekly hours are `time` values
--     interpreted in America/Phoenix (Arizona does not observe daylight saving).
--   * Row Level Security (RLS) is ON for every table. Anything involving money
--     or bookings is written only by our server code (Supabase "service role"),
--     never directly from the browser.
-- =============================================================================

create extension if not exists btree_gist;  -- lets us block double-bookings

-- -----------------------------------------------------------------------------
-- Enums (fixed lists of allowed values)
-- -----------------------------------------------------------------------------
create type public.user_role as enum ('family', 'coach', 'admin');

create type public.coach_status as enum ('pending', 'approved', 'rejected', 'suspended');

create type public.background_check_status as enum
  ('not_started', 'submitted', 'in_review', 'passed', 'failed', 'expired');

create type public.specialty as enum ('pitching', 'hitting', 'catching', 'strength');

create type public.booking_status as enum (
  'pending_payment',     -- slot is held for a few minutes while the family pays
  'confirmed',           -- paid (or covered by a package) and on the calendar
  'completed',           -- lesson time has passed
  'cancelled',           -- cancelled by family, coach, or admin
  'expired',             -- family never finished paying; slot released
  'no_show'
);

create type public.payment_status as enum
  ('pending', 'succeeded', 'failed', 'refunded', 'partially_refunded');

create type public.package_status as enum
  ('pending_payment', 'active', 'used_up', 'refunded', 'expired');

-- -----------------------------------------------------------------------------
-- Shared helpers
-- -----------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

-- -----------------------------------------------------------------------------
-- profiles: one row per login (families, coaches, admin)
-- -----------------------------------------------------------------------------
create table public.profiles (
  id          uuid primary key references auth.users (id) on delete cascade,
  role        public.user_role not null default 'family',
  full_name   text not null default '',
  email       text not null,
  phone       text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create trigger profiles_updated_at before update on public.profiles
  for each row execute function public.set_updated_at();

-- True when the logged-in user is the admin. "security definer" lets it read
-- profiles without tripping over profiles' own RLS rules.
create or replace function public.is_admin()
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.profiles where id = auth.uid() and role = 'admin');
$$;

-- True for our trusted server code (service role) and the Supabase SQL editor.
create or replace function public.is_server()
returns boolean language sql stable as $$
  select coalesce(auth.jwt() ->> 'role', 'service_role') = 'service_role';
$$;

-- Automatically create a profile when someone signs up. The sign-up form may
-- request 'family' or 'coach'; nobody can sign themselves up as admin.
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
declare
  requested text := new.raw_user_meta_data ->> 'role';
begin
  insert into public.profiles (id, email, full_name, role)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data ->> 'full_name', ''),
    case when requested = 'coach' then 'coach'::public.user_role else 'family'::public.user_role end
  );
  return new;
end $$;

create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();

-- Users may edit their own name/phone, but not promote their own role.
create or replace function public.guard_profile_role()
returns trigger language plpgsql as $$
begin
  if new.role is distinct from old.role and not (public.is_admin() or public.is_server()) then
    raise exception 'Only an admin can change a user role';
  end if;
  return new;
end $$;

create trigger profiles_guard_role before update on public.profiles
  for each row execute function public.guard_profile_role();

-- -----------------------------------------------------------------------------
-- coaches: the public coach profile + application status
-- -----------------------------------------------------------------------------
create table public.coaches (
  id                     uuid primary key default gen_random_uuid(),
  profile_id             uuid not null unique references public.profiles (id) on delete cascade,
  status                 public.coach_status not null default 'pending',
  slug                   text not null unique,            -- for URLs like /coaches/jake-martinez
  display_name           text not null,
  photo_url              text,
  bio                    text not null default '',
  playing_background     text not null default '',        -- e.g. "ASU pitcher, 3 yrs AA ball"
  specialties            public.specialty[] not null default '{}',
  lesson_price_cents     integer not null check (lesson_price_cents between 1000 and 100000),
  lesson_length_minutes  integer not null default 60 check (lesson_length_minutes in (30, 45, 60, 90)),
  location_name          text not null default '',        -- e.g. "Cactus Yards, Field 4"
  address                text not null default '',
  city                   text not null default '',        -- Phoenix, Scottsdale, Mesa, Gilbert...
  zip                    text,
  package_5_discount_pct  integer not null default 5  check (package_5_discount_pct between 0 and 50),
  package_10_discount_pct integer not null default 10 check (package_10_discount_pct between 0 and 50),
  approved_at            timestamptz,
  created_at             timestamptz not null default now(),
  updated_at             timestamptz not null default now()
);

create index coaches_status_idx on public.coaches (status);
create index coaches_city_idx on public.coaches (city);
create index coaches_specialties_idx on public.coaches using gin (specialties);

create trigger coaches_updated_at before update on public.coaches
  for each row execute function public.set_updated_at();

-- Coaches can edit their profile, but only the admin can approve/reject them.
create or replace function public.guard_coach_status()
returns trigger language plpgsql as $$
begin
  if (new.status is distinct from old.status or new.approved_at is distinct from old.approved_at)
     and not (public.is_admin() or public.is_server()) then
    raise exception 'Only an admin can change coach approval status';
  end if;
  return new;
end $$;

create trigger coaches_guard_status before update on public.coaches
  for each row execute function public.guard_coach_status();

-- Private coach info: never shown to families. Only the coach (read-only)
-- and the admin can see it; only admin/server can change it.
create table public.coach_private (
  coach_id                     uuid primary key references public.coaches (id) on delete cascade,
  -- application answers
  years_coaching               integer,
  certifications               text,
  references_text              text,
  why_join                     text,
  -- background check (manual for MVP)
  background_check_status      public.background_check_status not null default 'not_started',
  background_check_provider    text,
  background_check_completed_on date,
  background_check_expires_on  date,
  -- Stripe Connect
  stripe_account_id            text unique,
  stripe_onboarding_complete   boolean not null default false,
  -- admin only
  rejection_reason             text,
  admin_notes                  text,
  updated_at                   timestamptz not null default now()
);

create trigger coach_private_updated_at before update on public.coach_private
  for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- Availability
-- -----------------------------------------------------------------------------
-- Weekly recurring hours, e.g. "Tuesdays 4:00pm–8:00pm" (Phoenix time).
create table public.availability_rules (
  id           uuid primary key default gen_random_uuid(),
  coach_id     uuid not null references public.coaches (id) on delete cascade,
  day_of_week  smallint not null check (day_of_week between 0 and 6),  -- 0 = Sunday
  start_time   time not null,
  end_time     time not null,
  check (end_time > start_time)
);

create index availability_rules_coach_idx on public.availability_rules (coach_id);

-- One-off time off, e.g. "out of town Mar 3–5" or "busy Sat 9–11am".
create table public.availability_blocks (
  id         uuid primary key default gen_random_uuid(),
  coach_id   uuid not null references public.coaches (id) on delete cascade,
  starts_at  timestamptz not null,
  ends_at    timestamptz not null,
  reason     text,
  check (ends_at > starts_at)
);

create index availability_blocks_coach_idx on public.availability_blocks (coach_id, starts_at);

-- -----------------------------------------------------------------------------
-- Players (the kids) and liability waivers
-- -----------------------------------------------------------------------------
create table public.players (
  id          uuid primary key default gen_random_uuid(),
  family_id   uuid not null references public.profiles (id) on delete cascade,
  first_name  text not null,
  last_name   text not null default '',
  birth_date  date,                       -- age is calculated from this so it never goes stale
  position    text,                       -- e.g. "RHP / SS"
  bats        text check (bats in ('R', 'L', 'S')),
  throws      text check (throws in ('R', 'L')),
  notes       text,                       -- injuries, goals, anything the coach should know
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create index players_family_idx on public.players (family_id);

create trigger players_updated_at before update on public.players
  for each row execute function public.set_updated_at();

-- A parent signs once per waiver version (bump the version if the text changes).
create table public.waivers (
  id              uuid primary key default gen_random_uuid(),
  family_id       uuid not null references public.profiles (id) on delete cascade,
  waiver_version  text not null,
  signed_name     text not null,
  ip_address      text,
  user_agent      text,
  signed_at       timestamptz not null default now(),
  unique (family_id, waiver_version)
);

-- -----------------------------------------------------------------------------
-- Lesson packages (5 or 10 lessons with one coach, prepaid at a discount)
-- -----------------------------------------------------------------------------
create table public.package_purchases (
  id                    uuid primary key default gen_random_uuid(),
  family_id             uuid not null references public.profiles (id),
  coach_id              uuid not null references public.coaches (id),
  lesson_count          integer not null check (lesson_count in (5, 10)),
  lessons_remaining     integer not null check (lessons_remaining >= 0),
  unit_price_cents      integer not null,   -- coach's single-lesson price at time of purchase
  discount_pct          integer not null,
  total_price_cents     integer not null,
  platform_fee_cents    integer not null,   -- our 15%
  coach_payout_cents    integer not null,   -- the other 85%
  status                public.package_status not null default 'pending_payment',
  expires_at            timestamptz,        -- e.g. 12 months after purchase
  created_at            timestamptz not null default now(),
  check (lessons_remaining <= lesson_count)
);

create index package_purchases_family_idx on public.package_purchases (family_id);
create index package_purchases_coach_idx on public.package_purchases (coach_id);

-- -----------------------------------------------------------------------------
-- Bookings (one row = one lesson)
-- -----------------------------------------------------------------------------
create table public.bookings (
  id                    uuid primary key default gen_random_uuid(),
  coach_id              uuid not null references public.coaches (id),
  family_id             uuid not null references public.profiles (id),
  player_id             uuid not null references public.players (id),
  package_purchase_id   uuid references public.package_purchases (id),  -- set if paid with a package
  starts_at             timestamptz not null,
  ends_at               timestamptz not null,
  status                public.booking_status not null default 'pending_payment',
  hold_expires_at       timestamptz,          -- when an unpaid hold is released
  -- price snapshot (so later price changes don't rewrite history)
  price_cents           integer not null,
  platform_fee_cents    integer not null,
  coach_payout_cents    integer not null,
  -- location snapshot
  location_name         text not null default '',
  address               text not null default '',
  -- cancellation
  cancelled_at          timestamptz,
  cancelled_by          uuid references public.profiles (id),
  cancellation_reason   text,
  -- post-lesson note from coach to family
  coach_notes           text,
  coach_notes_at        timestamptz,
  -- email bookkeeping
  confirmation_sent_at  timestamptz,
  reminder_sent_at      timestamptz,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now(),
  check (ends_at > starts_at),
  check (platform_fee_cents + coach_payout_cents = price_cents),
  -- The database itself refuses two active bookings that overlap for one coach.
  constraint bookings_no_overlap exclude using gist (
    coach_id with =,
    tstzrange(starts_at, ends_at) with &&
  ) where (status in ('pending_payment', 'confirmed', 'completed'))
);

create index bookings_coach_time_idx on public.bookings (coach_id, starts_at);
create index bookings_family_idx on public.bookings (family_id, starts_at);
create index bookings_status_idx on public.bookings (status);

create trigger bookings_updated_at before update on public.bookings
  for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- Payments & refunds (a ledger of every Stripe charge — powers the admin
-- revenue/commission numbers)
-- -----------------------------------------------------------------------------
create table public.payments (
  id                          uuid primary key default gen_random_uuid(),
  family_id                   uuid not null references public.profiles (id),
  coach_id                    uuid not null references public.coaches (id),
  booking_id                  uuid references public.bookings (id),
  package_purchase_id         uuid references public.package_purchases (id),
  amount_cents                integer not null check (amount_cents > 0),
  platform_fee_cents          integer not null,
  coach_payout_cents          integer not null,
  refunded_cents              integer not null default 0,
  status                      public.payment_status not null default 'pending',
  stripe_checkout_session_id  text unique,
  stripe_payment_intent_id    text unique,
  created_at                  timestamptz not null default now(),
  updated_at                  timestamptz not null default now(),
  -- each payment is for exactly one thing: a single lesson OR a package
  check ((booking_id is null) <> (package_purchase_id is null))
);

create index payments_created_idx on public.payments (created_at);
create index payments_coach_idx on public.payments (coach_id);

create trigger payments_updated_at before update on public.payments
  for each row execute function public.set_updated_at();

create table public.refunds (
  id                uuid primary key default gen_random_uuid(),
  payment_id        uuid not null references public.payments (id),
  amount_cents      integer not null check (amount_cents > 0),
  reason            text,
  stripe_refund_id  text unique,
  issued_by         uuid references public.profiles (id),  -- null = automatic (policy cancel)
  created_at        timestamptz not null default now()
);

-- -----------------------------------------------------------------------------
-- Reviews (one per completed lesson)
-- -----------------------------------------------------------------------------
create table public.reviews (
  id          uuid primary key default gen_random_uuid(),
  booking_id  uuid not null unique references public.bookings (id),
  coach_id    uuid not null references public.coaches (id),
  family_id   uuid not null references public.profiles (id),
  rating      smallint not null check (rating between 1 and 5),
  comment     text,
  is_hidden   boolean not null default false,  -- admin can hide abusive reviews
  created_at  timestamptz not null default now()
);

create index reviews_coach_idx on public.reviews (coach_id);

-- Average rating per coach, always up to date (no stored copy to keep in sync).
create view public.coach_rating_summary with (security_invoker = true) as
  select coach_id,
         round(avg(rating)::numeric, 1) as avg_rating,
         count(*)::integer               as review_count
  from public.reviews
  where not is_hidden
  group by coach_id;

-- =============================================================================
-- Row Level Security (who can see / change what)
-- =============================================================================
alter table public.profiles            enable row level security;
alter table public.coaches             enable row level security;
alter table public.coach_private       enable row level security;
alter table public.availability_rules  enable row level security;
alter table public.availability_blocks enable row level security;
alter table public.players             enable row level security;
alter table public.waivers             enable row level security;
alter table public.package_purchases   enable row level security;
alter table public.bookings            enable row level security;
alter table public.payments            enable row level security;
alter table public.refunds             enable row level security;
alter table public.reviews             enable row level security;

-- Small helper: the coaches.id belonging to the logged-in user (or null).
create or replace function public.my_coach_id()
returns uuid language sql stable security definer set search_path = public as $$
  select id from public.coaches where profile_id = auth.uid();
$$;

-- profiles -------------------------------------------------------------------
create policy "read own profile" on public.profiles
  for select using (id = auth.uid() or public.is_admin());
create policy "coaches read families they have lessons with" on public.profiles
  for select using (exists (
    select 1 from public.bookings b
    where b.family_id = profiles.id and b.coach_id = public.my_coach_id()
  ));
create policy "update own profile" on public.profiles
  for update using (id = auth.uid() or public.is_admin());

-- coaches --------------------------------------------------------------------
create policy "anyone sees approved coaches" on public.coaches
  for select using (status = 'approved' or profile_id = auth.uid() or public.is_admin());
create policy "coach submits own application" on public.coaches
  for insert with check (profile_id = auth.uid() and status = 'pending');
create policy "coach edits own profile" on public.coaches
  for update using (profile_id = auth.uid() or public.is_admin());

-- coach_private --------------------------------------------------------------
create policy "coach reads own private row" on public.coach_private
  for select using (coach_id = public.my_coach_id() or public.is_admin());
create policy "coach submits own application details" on public.coach_private
  for insert with check (
    coach_id = public.my_coach_id()
    and background_check_status = 'not_started'
    and stripe_account_id is null
  );
create policy "admin edits private coach info" on public.coach_private
  for update using (public.is_admin());

-- availability ---------------------------------------------------------------
create policy "anyone reads availability" on public.availability_rules
  for select using (true);
create policy "coach manages own availability" on public.availability_rules
  for all using (coach_id = public.my_coach_id() or public.is_admin())
  with check (coach_id = public.my_coach_id() or public.is_admin());

create policy "anyone reads time off" on public.availability_blocks
  for select using (true);
create policy "coach manages own time off" on public.availability_blocks
  for all using (coach_id = public.my_coach_id() or public.is_admin())
  with check (coach_id = public.my_coach_id() or public.is_admin());

-- players --------------------------------------------------------------------
create policy "family manages own players" on public.players
  for all using (family_id = auth.uid()) with check (family_id = auth.uid());
create policy "coach reads players they coach" on public.players
  for select using (exists (
    select 1 from public.bookings b
    where b.player_id = players.id and b.coach_id = public.my_coach_id()
  ));
create policy "admin reads players" on public.players
  for select using (public.is_admin());

-- waivers --------------------------------------------------------------------
create policy "family signs waiver" on public.waivers
  for insert with check (family_id = auth.uid());
create policy "family/admin read waivers" on public.waivers
  for select using (family_id = auth.uid() or public.is_admin());

-- bookings, packages, payments, refunds: read-only from the browser.
-- All writes happen in server code with the service role key.
create policy "read own bookings" on public.bookings
  for select using (
    family_id = auth.uid() or coach_id = public.my_coach_id() or public.is_admin()
  );
create policy "read own packages" on public.package_purchases
  for select using (
    family_id = auth.uid() or coach_id = public.my_coach_id() or public.is_admin()
  );
create policy "read own payments" on public.payments
  for select using (
    family_id = auth.uid() or coach_id = public.my_coach_id() or public.is_admin()
  );
create policy "admin reads refunds" on public.refunds
  for select using (public.is_admin());

-- reviews --------------------------------------------------------------------
create policy "anyone reads visible reviews" on public.reviews
  for select using (not is_hidden or family_id = auth.uid() or public.is_admin());
create policy "family reviews own finished lesson" on public.reviews
  for insert with check (
    family_id = auth.uid()
    and exists (
      select 1 from public.bookings b
      where b.id = reviews.booking_id
        and b.family_id = auth.uid()
        and b.coach_id = reviews.coach_id
        and b.status in ('confirmed', 'completed')
        and b.ends_at < now()
    )
  );
create policy "admin moderates reviews" on public.reviews
  for update using (public.is_admin());

-- =============================================================================
-- Storage: public bucket for coach headshots. Each user uploads into a folder
-- named after their own user id, e.g. coach-photos/<user-id>/headshot.jpg
-- =============================================================================
insert into storage.buckets (id, name, public)
values ('coach-photos', 'coach-photos', true)
on conflict (id) do nothing;

create policy "anyone views coach photos" on storage.objects
  for select using (bucket_id = 'coach-photos');
create policy "users upload own coach photo" on storage.objects
  for insert with check (
    bucket_id = 'coach-photos' and (storage.foldername(name))[1] = auth.uid()::text
  );
create policy "users replace own coach photo" on storage.objects
  for update using (
    bucket_id = 'coach-photos' and (storage.foldername(name))[1] = auth.uid()::text
  );
