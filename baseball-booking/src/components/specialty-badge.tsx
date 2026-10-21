import { specialtyLabel } from "@/lib/constants";

export function SpecialtyBadge({ value }: { value: string }) {
  return (
    <span className="rounded-full border border-navy/15 bg-navy/5 px-2.5 py-0.5 text-xs font-semibold text-navy">
      {specialtyLabel(value)}
    </span>
  );
}
