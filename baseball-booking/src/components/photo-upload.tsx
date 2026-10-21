"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { CoachAvatar } from "./coach-avatar";

const MAX_SIDE = 800; // pixels; phone photos are shrunk to this before upload

/**
 * Lets a coach pick a headshot. The photo is shrunk in the browser (phone
 * photos can be 5MB+), uploaded to Supabase Storage, and its web address is
 * put in a hidden form field named "photo_url".
 */
export function PhotoUpload({
  userId,
  name,
  initialUrl,
}: {
  userId: string;
  name: string;
  initialUrl: string | null;
}) {
  const [url, setUrl] = useState(initialUrl ?? "");
  const [status, setStatus] = useState<"idle" | "uploading" | "error">("idle");

  async function onFile(file: File | undefined) {
    if (!file) return;
    setStatus("uploading");
    try {
      const blob = await shrinkImage(file);
      const supabase = createClient();
      const path = `${userId}/headshot-${Date.now()}.jpg`;
      const { error } = await supabase.storage
        .from("coach-photos")
        .upload(path, blob, { contentType: "image/jpeg", upsert: false });
      if (error) throw error;
      setUrl(supabase.storage.from("coach-photos").getPublicUrl(path).data.publicUrl);
      setStatus("idle");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div className="flex items-center gap-4">
      <CoachAvatar name={name || "?"} photoUrl={url || null} size={88} />
      <div>
        <label className="btn-outline cursor-pointer">
          {status === "uploading" ? "Uploading…" : url ? "Change photo" : "Add a photo"}
          <input
            type="file"
            accept="image/*"
            className="sr-only"
            onChange={(e) => onFile(e.target.files?.[0])}
            disabled={status === "uploading"}
          />
        </label>
        <p className="hint">
          {status === "error"
            ? "Upload failed. Try a different photo."
            : "A clear, friendly headshot. Families book coaches they can picture."}
        </p>
      </div>
      <input type="hidden" name="photo_url" value={url} />
    </div>
  );
}

async function shrinkImage(file: File): Promise<Blob> {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  canvas.getContext("2d")!.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  return new Promise((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("resize failed"))), "image/jpeg", 0.85),
  );
}
