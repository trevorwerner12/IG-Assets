-- =============================================================================
-- Nationwide support: coaches can be anywhere in the US.
-- =============================================================================
-- * state       2-letter code, e.g. 'AZ', 'TX'
-- * metro_area  the market families search by, e.g. 'Phoenix' or 'Houston'.
--               Suburbs roll up to their metro (Katy, TX -> 'Houston').
-- * timezone    the coach's local time zone. Weekly availability hours are
--               interpreted in this zone, and lesson times are shown in it
--               (the lesson happens where the coach is).
-- * latitude/longitude  optional, reserved for "coaches near me" search later.
-- =============================================================================

alter table public.coaches
  add column state      text not null default '' check (state = '' or state ~ '^[A-Z]{2}$'),
  add column metro_area text not null default '',
  add column timezone   text not null default 'America/Phoenix' check (timezone in (
    'America/New_York', 'America/Chicago', 'America/Denver', 'America/Phoenix',
    'America/Los_Angeles', 'America/Anchorage', 'Pacific/Honolulu'
  )),
  add column latitude   double precision check (latitude between -90 and 90),
  add column longitude  double precision check (longitude between -180 and 180);

create index coaches_metro_idx on public.coaches (metro_area);
create index coaches_state_city_idx on public.coaches (state, city);

comment on column public.availability_rules.start_time is
  'Local time in the coach''s time zone (coaches.timezone)';
comment on column public.availability_rules.end_time is
  'Local time in the coach''s time zone (coaches.timezone)';
