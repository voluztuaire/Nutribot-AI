// Local-only avatar storage. Photos are saved as data URLs in localStorage
// keyed by user id so we don't change the Flask backend contract.
import { useEffect, useState } from "react";

const KEY = (id: number | string) => `nutribot_avatar_${id}`;

export function getAvatar(userId?: number | string | null): string | null {
  if (typeof window === "undefined" || userId == null) return null;
  return localStorage.getItem(KEY(userId));
}

export function setAvatar(userId: number | string, dataUrl: string) {
  localStorage.setItem(KEY(userId), dataUrl);
  window.dispatchEvent(new CustomEvent("nutribot:avatar", { detail: { userId } }));
}

export function clearAvatar(userId: number | string) {
  localStorage.removeItem(KEY(userId));
  window.dispatchEvent(new CustomEvent("nutribot:avatar", { detail: { userId } }));
}

export function useAvatar(userId?: number | string | null) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    setUrl(getAvatar(userId));
    const h = () => setUrl(getAvatar(userId));
    window.addEventListener("nutribot:avatar", h);
    return () => window.removeEventListener("nutribot:avatar", h);
  }, [userId]);
  return url;
}

// Read a File as a resized data URL (max 256px square) so localStorage
// doesn't explode on large camera photos.
export async function fileToAvatarDataUrl(file: File, max = 256): Promise<string> {
  const buf = await file.arrayBuffer();
  const blob = new Blob([buf], { type: file.type });
  const img = await new Promise<HTMLImageElement>((resolve, reject) => {
    const i = new Image();
    i.onload = () => resolve(i);
    i.onerror = reject;
    i.src = URL.createObjectURL(blob);
  });
  const scale = Math.min(1, max / Math.max(img.width, img.height));
  const w = Math.round(img.width * scale);
  const h = Math.round(img.height * scale);
  const canvas = document.createElement("canvas");
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext("2d")!;
  ctx.drawImage(img, 0, 0, w, h);
  return canvas.toDataURL("image/jpeg", 0.85);
}
