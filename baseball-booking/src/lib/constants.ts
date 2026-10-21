export const SPECIALTIES = [
  { value: "pitching", label: "Pitching" },
  { value: "hitting", label: "Hitting" },
  { value: "catching", label: "Catching" },
  { value: "strength", label: "Strength & Speed" },
] as const;

export type Specialty = (typeof SPECIALTIES)[number]["value"];

export function specialtyLabel(value: string) {
  return SPECIALTIES.find((s) => s.value === value)?.label ?? value;
}

export const LESSON_LENGTHS = [30, 45, 60, 90] as const;

/**
 * Metro areas families search by. Suburbs belong to their metro
 * (e.g. Gilbert -> Phoenix, Katy -> Houston). Add new markets here.
 */
export const METRO_AREAS = [
  "Phoenix",
  "Houston",
  "Dallas–Fort Worth",
  "Austin",
  "San Antonio",
  "Los Angeles",
  "San Diego",
  "Las Vegas",
  "Denver",
  "Atlanta",
  "Tampa",
  "Orlando",
  "Miami",
  "Chicago",
  "New York",
  "Other",
] as const;

export const TIMEZONES = [
  { value: "America/New_York", label: "Eastern" },
  { value: "America/Chicago", label: "Central" },
  { value: "America/Denver", label: "Mountain" },
  { value: "America/Phoenix", label: "Arizona (no daylight saving)" },
  { value: "America/Los_Angeles", label: "Pacific" },
  { value: "America/Anchorage", label: "Alaska" },
  { value: "Pacific/Honolulu", label: "Hawaii" },
] as const;

export type Timezone = (typeof TIMEZONES)[number]["value"];

// Each state's main time zone. A few states span two zones (e.g. far west
// Texas), so coaches can still change it on their profile.
const EASTERN = "America/New_York";
const CENTRAL = "America/Chicago";
const MOUNTAIN = "America/Denver";
const PACIFIC = "America/Los_Angeles";

export const US_STATES: { code: string; name: string; tz: Timezone }[] = [
  { code: "AL", name: "Alabama", tz: CENTRAL },
  { code: "AK", name: "Alaska", tz: "America/Anchorage" },
  { code: "AZ", name: "Arizona", tz: "America/Phoenix" },
  { code: "AR", name: "Arkansas", tz: CENTRAL },
  { code: "CA", name: "California", tz: PACIFIC },
  { code: "CO", name: "Colorado", tz: MOUNTAIN },
  { code: "CT", name: "Connecticut", tz: EASTERN },
  { code: "DE", name: "Delaware", tz: EASTERN },
  { code: "DC", name: "District of Columbia", tz: EASTERN },
  { code: "FL", name: "Florida", tz: EASTERN },
  { code: "GA", name: "Georgia", tz: EASTERN },
  { code: "HI", name: "Hawaii", tz: "Pacific/Honolulu" },
  { code: "ID", name: "Idaho", tz: MOUNTAIN },
  { code: "IL", name: "Illinois", tz: CENTRAL },
  { code: "IN", name: "Indiana", tz: EASTERN },
  { code: "IA", name: "Iowa", tz: CENTRAL },
  { code: "KS", name: "Kansas", tz: CENTRAL },
  { code: "KY", name: "Kentucky", tz: EASTERN },
  { code: "LA", name: "Louisiana", tz: CENTRAL },
  { code: "ME", name: "Maine", tz: EASTERN },
  { code: "MD", name: "Maryland", tz: EASTERN },
  { code: "MA", name: "Massachusetts", tz: EASTERN },
  { code: "MI", name: "Michigan", tz: EASTERN },
  { code: "MN", name: "Minnesota", tz: CENTRAL },
  { code: "MS", name: "Mississippi", tz: CENTRAL },
  { code: "MO", name: "Missouri", tz: CENTRAL },
  { code: "MT", name: "Montana", tz: MOUNTAIN },
  { code: "NE", name: "Nebraska", tz: CENTRAL },
  { code: "NV", name: "Nevada", tz: PACIFIC },
  { code: "NH", name: "New Hampshire", tz: EASTERN },
  { code: "NJ", name: "New Jersey", tz: EASTERN },
  { code: "NM", name: "New Mexico", tz: MOUNTAIN },
  { code: "NY", name: "New York", tz: EASTERN },
  { code: "NC", name: "North Carolina", tz: EASTERN },
  { code: "ND", name: "North Dakota", tz: CENTRAL },
  { code: "OH", name: "Ohio", tz: EASTERN },
  { code: "OK", name: "Oklahoma", tz: CENTRAL },
  { code: "OR", name: "Oregon", tz: PACIFIC },
  { code: "PA", name: "Pennsylvania", tz: EASTERN },
  { code: "RI", name: "Rhode Island", tz: EASTERN },
  { code: "SC", name: "South Carolina", tz: EASTERN },
  { code: "SD", name: "South Dakota", tz: CENTRAL },
  { code: "TN", name: "Tennessee", tz: CENTRAL },
  { code: "TX", name: "Texas", tz: CENTRAL },
  { code: "UT", name: "Utah", tz: MOUNTAIN },
  { code: "VT", name: "Vermont", tz: EASTERN },
  { code: "VA", name: "Virginia", tz: EASTERN },
  { code: "WA", name: "Washington", tz: PACIFIC },
  { code: "WV", name: "West Virginia", tz: EASTERN },
  { code: "WI", name: "Wisconsin", tz: CENTRAL },
  { code: "WY", name: "Wyoming", tz: MOUNTAIN },
];

export function defaultTimezoneForState(code: string): Timezone {
  return US_STATES.find((s) => s.code === code)?.tz ?? "America/Phoenix";
}
