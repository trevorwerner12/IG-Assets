/**
 * Adds sample coaches (Phoenix + Houston areas), a demo family, and a few
 * reviews so you have something to click around. Safe to run more than once;
 * it skips if the sample data is already there.
 *
 *   npm run seed
 *
 * Sample logins (password for all: Practice123!):
 *   demo-family@example.com          a parent account
 *   coach.<first name>@example.com   e.g. coach.marcus@example.com
 */
import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const key = process.env.SUPABASE_SECRET_KEY;
if (!url || !key) {
  console.error("Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SECRET_KEY in .env.local");
  process.exit(1);
}
const db = createClient(url, key, { auth: { persistSession: false } });
const PASSWORD = "Practice123!";

type SeedCoach = {
  first: string;
  name: string;
  city: string;
  state: string;
  zip: string;
  metro: string;
  timezone: string;
  location: string;
  price: number;
  length: number;
  specialties: string[];
  background: string;
  bio: string;
  ratings: number[];
};

const COACHES: SeedCoach[] = [
  {
    first: "marcus", name: "Marcus Delgado", city: "Gilbert", state: "AZ", zip: "85296",
    metro: "Phoenix", timezone: "America/Phoenix", location: "Freestone Park Field 3",
    price: 75, length: 60, specialties: ["pitching"], ratings: [5, 5, 4],
    background: "Pitched 4 years at Arizona State. Drafted in the 14th round and spent 3 seasons in the minors.",
    bio: "I focus on clean, repeatable mechanics and arm care first, then velocity. I work with players ages 9 to 18 and send a short video breakdown after every lesson.",
  },
  {
    first: "tasha", name: "Tasha Reynolds", city: "Scottsdale", state: "AZ", zip: "85258",
    metro: "Phoenix", timezone: "America/Phoenix", location: "Indian School Park",
    price: 65, length: 60, specialties: ["hitting", "strength"], ratings: [5, 5],
    background: "All-conference outfielder at Grand Canyon University. Certified strength and conditioning coach.",
    bio: "Hitting is about timing and a simple approach. We'll build a swing your kid can repeat under game pressure, plus the strength to drive the ball.",
  },
  {
    first: "luis", name: "Luis Ortega", city: "Mesa", state: "AZ", zip: "85201",
    metro: "Phoenix", timezone: "America/Phoenix", location: "Mesa Riverview Cages",
    price: 55, length: 45, specialties: ["catching", "hitting"], ratings: [4, 5, 5, 5],
    background: "Catcher at Mesa Community College, then at New Mexico State. 8 years coaching travel ball.",
    bio: "Catchers run the field. I teach receiving, blocking, and quick, accurate throws, along with how to lead a pitching staff.",
  },
  {
    first: "derek", name: "Derek Chen", city: "Peoria", state: "AZ", zip: "85382",
    metro: "Phoenix", timezone: "America/Phoenix", location: "Peoria Sports Complex, back fields",
    price: 90, length: 60, specialties: ["pitching", "strength"], ratings: [],
    background: "Former Division I pitching coach. Driveline-certified.",
    bio: "Data-driven pitching development for serious high school players: velocity programs, pitch design, and recovery.",
  },
  {
    first: "jamal", name: "Jamal Washington", city: "Katy", state: "TX", zip: "77494",
    metro: "Houston", timezone: "America/Chicago", location: "Katy Baseball Academy",
    price: 70, length: 60, specialties: ["hitting"], ratings: [5, 4, 5],
    background: "Played 3 years at the University of Houston. Hitting coach for a 17U national travel team.",
    bio: "I teach hitters to understand their own swing. Expect lots of reps, clear feedback, and drills to take home.",
  },
  {
    first: "brooke", name: "Brooke Alvarez", city: "Sugar Land", state: "TX", zip: "77479",
    metro: "Houston", timezone: "America/Chicago", location: "Imperial Park Fields",
    price: 60, length: 60, specialties: ["pitching", "catching"], ratings: [5],
    background: "Pitched and caught at Rice University. 6 years of private instruction.",
    bio: "Patient, positive coaching for younger players building their foundation. I love working with 8 to 13 year olds.",
  },
  {
    first: "tony", name: "Tony Russo", city: "The Woodlands", state: "TX", zip: "77380",
    metro: "Houston", timezone: "America/Chicago", location: "Bear Branch Sportsfields",
    price: 85, length: 60, specialties: ["strength", "hitting"], ratings: [4, 5],
    background: "Minor league infielder (Astros organization), now a CSCS strength coach.",
    bio: "Get stronger, faster, and more explosive with baseball-specific training that's safe for young athletes.",
  },
  {
    first: "kevin", name: "Kevin Park", city: "Pearland", state: "TX", zip: "77584",
    metro: "Houston", timezone: "America/Chicago", location: "Centennial Park",
    price: 50, length: 30, specialties: ["catching"], ratings: [],
    background: "4-year starting catcher at Sam Houston State.",
    bio: "Short, focused catching sessions on footwork, blocking, and pop time.",
  },
];

async function createUser(email: string, fullName: string, role: "family" | "coach") {
  const { data, error } = await db.auth.admin.createUser({
    email,
    password: PASSWORD,
    email_confirm: true,
    user_metadata: { full_name: fullName, role },
  });
  if (error) throw new Error(`${email}: ${error.message}`);
  return data.user.id;
}

async function main() {
  const { data: existing } = await db.from("coaches").select("id").eq("slug", "marcus-delgado");
  if (existing?.length) {
    console.log("Sample data is already there. Nothing to do.");
    return;
  }

  console.log("Creating demo family…");
  const familyId = await createUser("demo-family@example.com", "Demo Parent", "family");
  const { data: player, error: playerError } = await db
    .from("players")
    .insert({ family_id: familyId, first_name: "Tommy", last_name: "Parent", birth_date: "2014-05-01", position: "SS / RHP" })
    .select("id")
    .single();
  if (playerError) throw playerError;

  let dayOffset = 60;
  for (const c of COACHES) {
    console.log(`Creating coach ${c.name}…`);
    const profileId = await createUser(`coach.${c.first}@example.com`, c.name, "coach");
    const { data: coach, error } = await db
      .from("coaches")
      .insert({
        profile_id: profileId,
        slug: c.name.toLowerCase().replace(/[^a-z]+/g, "-"),
        status: "approved",
        approved_at: new Date().toISOString(),
        display_name: c.name,
        bio: c.bio,
        playing_background: c.background,
        specialties: c.specialties,
        lesson_price_cents: c.price * 100,
        lesson_length_minutes: c.length,
        location_name: c.location,
        address: "",
        city: c.city,
        state: c.state,
        zip: c.zip,
        metro_area: c.metro,
        timezone: c.timezone,
      })
      .select("id")
      .single();
    if (error) throw error;

    await db.from("coach_private").insert({
      coach_id: coach.id,
      years_coaching: 5,
      references_text: "Sample data",
      background_check_status: "passed",
      background_check_provider: "Sample",
    });

    // Past lessons with reviews, so ratings show up.
    for (const rating of c.ratings) {
      const starts = new Date(Date.now() - dayOffset-- * 86_400_000);
      starts.setUTCHours(1, 0, 0, 0);
      const ends = new Date(starts.getTime() + c.length * 60_000);
      const price = c.price * 100;
      const fee = Math.round(price * 0.15);
      const { data: booking, error: bookingError } = await db
        .from("bookings")
        .insert({
          coach_id: coach.id,
          family_id: familyId,
          player_id: player.id,
          starts_at: starts.toISOString(),
          ends_at: ends.toISOString(),
          status: "completed",
          price_cents: price,
          platform_fee_cents: fee,
          coach_payout_cents: price - fee,
          location_name: c.location,
        })
        .select("id")
        .single();
      if (bookingError) throw bookingError;
      await db.from("reviews").insert({
        booking_id: booking.id,
        coach_id: coach.id,
        family_id: familyId,
        rating,
        comment: rating === 5 ? "Fantastic with my son. He's already seeing results!" : "Really helpful lesson, good drills to practice at home.",
      });
    }
  }
  console.log(`\nDone! Log in as demo-family@example.com or coach.marcus@example.com (password: ${PASSWORD})`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
