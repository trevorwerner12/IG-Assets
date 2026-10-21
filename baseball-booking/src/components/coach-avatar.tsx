import Image from "next/image";
import { initials } from "@/lib/format";

export function CoachAvatar({
  name,
  photoUrl,
  size = 80,
  className = "",
}: {
  name: string;
  photoUrl: string | null;
  size?: number;
  className?: string;
}) {
  if (photoUrl) {
    return (
      <Image
        src={photoUrl}
        alt={`Photo of ${name}`}
        width={size}
        height={size}
        className={`shrink-0 rounded-2xl object-cover ${className}`}
        style={{ width: size, height: size }}
      />
    );
  }
  return (
    <div
      aria-hidden="true"
      className={`flex shrink-0 items-center justify-center rounded-2xl bg-navy font-display font-bold text-white ${className}`}
      style={{ width: size, height: size, fontSize: size * 0.38 }}
    >
      {initials(name)}
    </div>
  );
}
