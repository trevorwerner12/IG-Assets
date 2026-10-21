# Database schema: plain-English guide

The SQL is in `supabase/migrations/20261021000000_initial_schema.sql`.
This page explains what each table is for and how they connect.

## The big picture

```
                        auth.users  (Supabase handles email login)
                             │ 1:1
                         profiles  (role: family | coach | admin)
          ┌──────────────────┼─────────────────────────┐
          │ family           │ coach                   │
     players (kids)       coaches ──1:1── coach_private (background check,
     waivers                 │                          Stripe account, application)
                             ├── availability_rules  (weekly hours)
                             └── availability_blocks (time off)

  bookings ─── one lesson: family + player + coach + time + price split
     │   └── (optional) package_purchase_id → package_purchases (5 or 10 pack)
     ├── payments ─── every Stripe charge (single lesson OR package)
     │      └── refunds
     └── reviews  (one per finished lesson) → coach_rating_summary (avg stars)
```

## Tables

| Table | What it holds | Who can see it |
|---|---|---|
| **profiles** | One row per login: name, email, phone, and **role** (family, coach, or admin). Created automatically when someone signs up. | You see your own. Coaches see the parents of kids they coach. Admin sees all. |
| **coaches** | The public profile: photo, bio, playing background, specialties, price, lesson length, location, city, package discounts, **status** (pending, approved, rejected, or suspended). | Anyone can see **approved** coaches. A coach sees their own profile even while it's pending. |
| **coach_private** | Information families should never see: application answers, **background check status**, Stripe account ID, rejection reason, admin notes. | The coach (read only) and the admin. |
| **availability_rules** | Weekly hours, e.g. "Tuesday 4–8pm". Open time slots are calculated from these. | Anyone (needed to show open slots). Each coach edits only their own. |
| **availability_blocks** | One-off time off, e.g. "out of town March 3–5". | Same as above. |
| **players** | Your kids: name, birth date (age is calculated from it), position, bats/throws, notes. | The family. A coach sees a player only after that player books with them. |
| **waivers** | Proof that a parent signed the liability waiver: typed name, time, IP address, waiver version. | The family and the admin. |
| **package_purchases** | A 5- or 10-lesson pack with one coach: price, discount, how many lessons are left. | The family, that coach, and the admin. |
| **bookings** | One lesson: who, when, where, its status, and the **price split** (price = platform fee + coach payout). Also holds the coach's post-lesson note and whether reminder emails went out. | The family, that coach, and the admin. |
| **payments** | Every Stripe charge, with amount, our fee, the coach's share, and how much was refunded. The admin revenue numbers come from this table. | The family, that coach, and the admin. |
| **refunds** | Each refund issued, who issued it, and why. | Admin. |
| **reviews** | 1–5 stars plus a comment, one per lesson. The admin can hide abusive reviews. | Anyone can read visible reviews. |
| **coach_rating_summary** | Not a table. It's a live calculation of each coach's average rating and review count. | Anyone. |

## Safety rules built into the database

These are enforced by the database itself, so a bug in our page code can't break them:

1. **No double-booking.** The database refuses two active lessons for the same coach at overlapping times. Back-to-back lessons are fine.
2. **The fee math always adds up.** On every booking, `platform_fee + coach_payout = price`.
3. **Nobody can make themselves admin.** Sign-up only allows "family" or "coach". You make yourself admin once, by hand (see the README).
4. **Coaches can't approve themselves.** Only the admin can change a coach's status.
5. **Families can't see pending coaches.** A profile goes live only after approval.
6. **The browser never writes money or bookings directly.** Bookings, payments, packages, and refunds are created only by our server code, after Stripe confirms payment.
7. **You can only review your own lesson,** and only after it has happened.
8. **Families can't see each other's kids or bookings.**

## Decisions you may want to weigh in on

These are my defaults. Any of them is easy to change now and harder to change later.

- **Unpaid holds:** when a parent picks a time, that slot is held for about 10 minutes while they pay on Stripe. If they abandon checkout, the slot opens up again.
- **Packages are tied to one coach.** A 10-pack with Coach Jake is used only with Jake. Default discounts are 5% for 5 lessons and 10% for 10 lessons, and each coach can change their own. The coach is paid for the whole pack when it's bought, minus the 15% fee. Packages expire 12 months after purchase.
- **Cancellation policy:** cancel more than 24 hours ahead and you get a full refund (or the lesson goes back on your package). Cancel later than that and there's no refund. The 24 hours will be one setting in the code.
- **One location per coach** for the MVP. Multiple facilities can come later.
- **Age:** we store the birth date rather than the age, so a player's age is always current.
- **Waiver:** one signature per family, covering all their kids. If you change the waiver text, every family re-signs once.
- **Time zone:** everything is shown in Arizona time (America/Phoenix, which has no daylight saving time).
