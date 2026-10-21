/** 6500 -> "$65" ; 6550 -> "$65.50" */
export function formatPrice(cents: number) {
  const dollars = cents / 100;
  return dollars.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: Number.isInteger(dollars) ? 0 : 2,
  });
}

/** Price of a 5- or 10-lesson package after the coach's discount. */
export function packagePriceCents(unitCents: number, count: number, discountPct: number) {
  return Math.round((unitCents * count * (100 - discountPct)) / 100);
}

export function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]!.toUpperCase())
    .join("");
}

/** "Jake Martínez" -> "jake-martinez" */
export function slugify(text: string) {
  return text
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60);
}
