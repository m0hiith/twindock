// Export PNG / PDF of the current /wiring view. The view's SVG is cloned at its full extent (not the
// current pan/zoom), framed with a title and legend, rasterised on a canvas, and either downloaded
// as PNG or wrapped in a one-page A4 landscape PDF (a JPEG on a page: no PDF library needed).
import { color } from "../theme";
import { WIRE_HEX } from "./model";
import { FONT } from "./ui";

const MARGIN = 40;
const HEADER = 96;
const FOOTER = 64;
const SCALE = 2;

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

async function toDataUrl(url: string): Promise<string | null> {
  try {
    const r = await fetch(url);
    const type = r.headers.get("content-type") ?? "";
    if (!r.ok || !type.startsWith("image/")) return null;
    const blob = await r.blob();
    return await new Promise((resolve) => {
      const fr = new FileReader();
      fr.onload = () => resolve(String(fr.result));
      fr.onerror = () => resolve(null);
      fr.readAsDataURL(blob);
    });
  } catch {
    return null;
  }
}

function legend(y: number, showWires: boolean): string {
  let x = MARGIN;
  const parts: string[] = [];
  const item = (swatch: string, label: string, w: number) => {
    parts.push(`<g transform="translate(${x},${y})">${swatch}<text x="34" y="5" font-size="13" fill="${color.ink}">${esc(label)}</text></g>`);
    x += w;
  };
  item(`<rect x="0" y="-8" width="26" height="16" rx="3" fill="#F1F1F1" stroke="${color.idle}" stroke-dasharray="5 3"/>`, "Planned · not connected yet", 230);
  item(`<rect x="0" y="-8" width="26" height="16" rx="3" fill="#2E2E2E" stroke="#111"/>`, "Wired", 100);
  item(`<rect x="0" y="-8" width="26" height="16" rx="3" fill="#FFF" stroke="${color.ok}" stroke-width="2"/>`, "Verified · firmware read it", 230);
  if (showWires) {
    for (const [c, l] of [["red", "3.3 V"], ["black", "GND"], ["blue", "SDA"], ["yellow", "SCL"]] as const) {
      item(`<line x1="0" y1="0" x2="26" y2="0" stroke="${WIRE_HEX[c]}" stroke-width="4" stroke-linecap="round"/>`, l, 90);
    }
  }
  return parts.join("");
}

export async function renderView(svg: SVGSVGElement, title: string, subtitle: string, showWires: boolean): Promise<HTMLCanvasElement> {
  const W = Number(svg.dataset.fullW);
  const H = Number(svg.dataset.fullH);
  const clone = svg.cloneNode(true) as SVGSVGElement;
  clone.querySelectorAll("[data-export-skip]").forEach((n) => n.remove());
  for (const img of clone.querySelectorAll("image")) {
    const href = img.getAttribute("href");
    const data = href ? await toDataUrl(href) : null;
    if (data) img.setAttribute("href", data);
    else img.remove();
  }
  clone.setAttribute("viewBox", `0 0 ${W} ${H}`);
  clone.setAttribute("x", String(MARGIN));
  clone.setAttribute("y", String(HEADER));
  clone.setAttribute("width", String(W));
  clone.setAttribute("height", String(H));
  clone.removeAttribute("class");
  clone.removeAttribute("style");

  const logo = await toDataUrl("/brand/silicon-labs.png");
  const OW = W + MARGIN * 2;
  const OH = HEADER + H + FOOTER;
  const doc = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${OW}" height="${OH}" viewBox="0 0 ${OW} ${OH}" font-family="${esc(FONT)}">
<rect width="${OW}" height="${OH}" fill="#FFFFFF"/>
${logo ? `<image href="${logo}" x="${MARGIN}" y="24" height="20" width="182"/>` : ""}
<text x="${MARGIN + (logo ? 196 : 0)}" y="40" font-size="20" font-weight="600" fill="${color.ink}">TwinDock · ${esc(title)}</text>
<text x="${MARGIN}" y="70" font-size="13" fill="${color.ink2}">${esc(subtitle)}</text>
<line x1="${MARGIN}" x2="${OW - MARGIN}" y1="${HEADER - 12}" y2="${HEADER - 12}" stroke="${color.cardBorder}"/>
${new XMLSerializer().serializeToString(clone)}
${legend(HEADER + H + 32, showWires)}
</svg>`;

  const url = URL.createObjectURL(new Blob([doc], { type: "image/svg+xml;charset=utf-8" }));
  try {
    const img = new Image();
    img.decoding = "sync";
    await new Promise<void>((resolve, reject) => {
      img.onload = () => resolve();
      img.onerror = () => reject(new Error("could not render the view"));
      img.src = url;
    });
    const canvas = document.createElement("canvas");
    canvas.width = OW * SCALE;
    canvas.height = OH * SCALE;
    const g = canvas.getContext("2d")!;
    g.fillStyle = "#FFFFFF";
    g.fillRect(0, 0, canvas.width, canvas.height);
    g.drawImage(img, 0, 0, canvas.width, canvas.height);
    return canvas;
  } finally {
    URL.revokeObjectURL(url);
  }
}

function download(blob: Blob, filename: string): void {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

export async function exportPng(canvas: HTMLCanvasElement, filename: string): Promise<void> {
  const blob = await new Promise<Blob | null>((r) => canvas.toBlob(r, "image/png"));
  if (!blob) throw new Error("PNG encoding failed");
  download(blob, filename);
}

export function exportPdf(canvas: HTMLCanvasElement, filename: string): void {
  download(new Blob([pdfFromJpeg(canvas)], { type: "application/pdf" }), filename);
}

/** One A4 landscape page with the canvas as a JPEG (DCTDecode), centred with 24 pt margins. */
function pdfFromJpeg(canvas: HTMLCanvasElement): Uint8Array<ArrayBuffer> {
  const b64 = canvas.toDataURL("image/jpeg", 0.92).split(",")[1]!;
  const jpeg = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  const PW = 842;
  const PH = 595;
  const m = 24;
  const s = Math.min((PW - 2 * m) / canvas.width, (PH - 2 * m) / canvas.height);
  const w = canvas.width * s;
  const h = canvas.height * s;
  const content = `q ${w.toFixed(2)} 0 0 ${h.toFixed(2)} ${((PW - w) / 2).toFixed(2)} ${((PH - h) / 2).toFixed(2)} cm /Im0 Do Q`;

  const enc = new TextEncoder();
  const chunks: Uint8Array[] = [];
  const offsets: number[] = [];
  let pos = 0;
  const push = (b: Uint8Array | string) => {
    const u = typeof b === "string" ? enc.encode(b) : b;
    chunks.push(u);
    pos += u.length;
  };
  const obj = (n: number, body: string | (() => void)) => {
    offsets[n] = pos;
    push(`${n} 0 obj\n`);
    if (typeof body === "string") push(body);
    else body();
    push("\nendobj\n");
  };
  push("%PDF-1.4\n%\xE2\xE3\xCF\xD3\n");
  obj(1, "<< /Type /Catalog /Pages 2 0 R >>");
  obj(2, "<< /Type /Pages /Kids [3 0 R] /Count 1 >>");
  obj(3, `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${PW} ${PH}] /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>`);
  obj(4, () => {
    push(`<< /Type /XObject /Subtype /Image /Width ${canvas.width} /Height ${canvas.height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${jpeg.length} >>\nstream\n`);
    push(jpeg);
    push("\nendstream");
  });
  obj(5, `<< /Length ${content.length} >>\nstream\n${content}\nendstream`);
  const xref = pos;
  push(`xref\n0 6\n0000000000 65535 f \n${offsets.slice(1).map((o) => `${String(o).padStart(10, "0")} 00000 n \n`).join("")}`);
  push(`trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`);

  const out = new Uint8Array(pos);
  let at = 0;
  for (const c of chunks) {
    out.set(c, at);
    at += c.length;
  }
  return out;
}
