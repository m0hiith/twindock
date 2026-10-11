// The board photo (frontend/public/board/top.jpg), used by the breadboard view once it exists.
import { useEffect, useState } from "react";

export type PhotoState = "checking" | "photo" | "none";
export const BOARD_PHOTO = "/board/top.jpg";

/** "photo" as soon as the file exists, "none" until then (the view draws the UG581 outline).
 *  Probed with an Image because the dev server and Vercel answer a missing file with index.html (200). */
export function useBoardPhoto(): PhotoState {
  const [state, setState] = useState<PhotoState>("checking");
  useEffect(() => {
    const img = new Image();
    img.onload = () => setState(img.naturalWidth > 0 ? "photo" : "none");
    img.onerror = () => setState("none");
    img.src = BOARD_PHOTO;
  }, []);
  return state;
}

export const partPhotoUrl = (partId: string) => `/parts/${partId}.jpg`;

/** Parts that have their own photo in frontend/public/parts/<part_id>.jpg (my own photo or a licensed image listed in
 *  CREDITS.md). Probed with an Image for the same reason as the board photo. */
export function usePartPhotos(ids: readonly string[]): ReadonlySet<string> {
  const [have, setHave] = useState<ReadonlySet<string>>(new Set());
  const key = ids.join(",");
  useEffect(() => {
    let alive = true;
    for (const id of key ? key.split(",") : []) {
      const img = new Image();
      img.onload = () => { if (alive && img.naturalWidth > 0) setHave((s) => new Set([...s, id])); };
      img.src = partPhotoUrl(id);
    }
    return () => { alive = false; };
  }, [key]);
  return have;
}
