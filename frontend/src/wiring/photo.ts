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
