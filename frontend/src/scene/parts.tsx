// Shared low-poly building blocks. Geometry and materials are cached so hundreds of parts cost
// a handful of GPU objects; every part can show the hover outline via OutlineContext.
import { createContext, useContext, useMemo, type ReactNode } from "react";
import * as THREE from "three";
import { color, font } from "../theme";

const materials = new Map<string, THREE.MeshStandardMaterial>();
export function mat(hex: string, opts: { emissive?: string; transparent?: number } = {}): THREE.MeshStandardMaterial {
  const key = `${hex}|${opts.emissive ?? ""}|${opts.transparent ?? ""}`;
  let m = materials.get(key);
  if (!m) {
    m = new THREE.MeshStandardMaterial({ color: hex, roughness: 0.85, metalness: 0 });
    if (opts.emissive) {
      m.emissive = new THREE.Color(opts.emissive);
      m.emissiveIntensity = 0.9;
    }
    if (opts.transparent !== undefined) {
      m.transparent = true;
      m.opacity = opts.transparent;
      m.depthWrite = false;
    }
    materials.set(key, m);
  }
  return m;
}

export const unitBox = new THREE.BoxGeometry(1, 1, 1);
export const unitCyl = new THREE.CylinderGeometry(0.5, 0.5, 1, 14);
export const unitSphere = new THREE.IcosahedronGeometry(0.5, 1);
export const unitPlane = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);

export const OutlineContext = createContext(false);

/** Unbaked parts (the moving forks) get a back-face hull when their unit is hovered. */
const hoverMat = new THREE.MeshBasicMaterial({ color: color.accent, side: THREE.BackSide });
function HoverOutline() {
  const on = useContext(OutlineContext);
  return on ? <mesh geometry={unitBox} material={hoverMat} scale={[1.08, 1.6, 1.4]} /> : null;
}

type V3 = [number, number, number];

interface PartProps {
  size: V3;
  at?: V3; // centre of the bottom face, so parts stack by height
  rot?: V3;
  color?: string;
  material?: THREE.Material;
  shadow?: boolean;
  children?: ReactNode;
}

/** Box whose `at` is the centre of its bottom face. */
export function Box({ size, at = [0, 0, 0], rot, color: c = "#ffffff", material, shadow = true }: PartProps) {
  return (
    <mesh geometry={unitBox} material={material ?? mat(c)} scale={size} rotation={rot}
      position={[at[0], at[1] + size[1] / 2, at[2]]} castShadow={shadow} receiveShadow>
      <HoverOutline />
    </mesh>
  );
}

/** Cylinder; `axis` "x" lays it on its side (wheels, rolled doors). */
export function Cyl({ size, at = [0, 0, 0], color: c = "#ffffff", material, shadow = true, axis = "y" }:
  PartProps & { axis?: "x" | "y" | "z" }) {
  const rot: V3 = axis === "x" ? [0, 0, Math.PI / 2] : axis === "z" ? [Math.PI / 2, 0, 0] : [0, 0, 0];
  return (
    <mesh geometry={unitCyl} material={material ?? mat(c)} scale={size} rotation={rot} position={at} castShadow={shadow}>
      <HoverOutline />
    </mesh>
  );
}

export function Ball({ size, at = [0, 0, 0], color: c = "#ffffff", shadow = true }: PartProps) {
  return (
    <mesh geometry={unitSphere} material={mat(c)} scale={size} position={at} castShadow={shadow}>
      <HoverOutline />
    </mesh>
  );
}

/** Flat ground decal (markings, outlines). y is a tiny lift to avoid z-fighting. */
export function Decal({ x, z, w, d, c, y = 0.02, rot = 0, opacity }: { x: number; z: number; w: number; d: number; c: string; y?: number; rot?: number; opacity?: number }) {
  return <mesh geometry={unitPlane} material={mat(c, opacity !== undefined ? { transparent: opacity } : {})}
    position={[x, y, z]} scale={[w, 1, d]} rotation={[0, rot, 0]} receiveShadow />;
}

const textures = new Map<string, THREE.CanvasTexture>();
/**
 * Text drawn into a canvas texture (wordmarks, door and zone labels). Canvas text uses the page's
 * Inter webfont, so no font file has to be shipped for three.js.
 */
export function useTextTexture(text: string, opts: { color?: string; bg?: string; weight?: number; px?: number; w?: number; h?: number } = {}) {
  const { color: fg = color.ink, bg = "transparent", weight = 600, px = 64, w = 512, h = 128 } = opts;
  return useMemo(() => {
    const key = [text, fg, bg, weight, px, w, h].join("|");
    let t = textures.get(key);
    if (t) return t;
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d")!;
    if (bg !== "transparent") {
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, w, h);
    }
    ctx.fillStyle = fg;
    ctx.font = `${weight} ${px}px ${font.family}`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(text, w / 2, h / 2 + px * 0.04);
    t = new THREE.CanvasTexture(canvas);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 4;
    textures.set(key, t);
    // Redraw once Inter has loaded, in case the first draw used the fallback font.
    void document.fonts?.ready.then(() => {
      ctx.clearRect(0, 0, w, h);
      if (bg !== "transparent") {
        ctx.fillStyle = bg;
        ctx.fillRect(0, 0, w, h);
      }
      ctx.fillStyle = fg;
      ctx.font = `${weight} ${px}px ${font.family}`;
      ctx.fillText(text, w / 2, h / 2 + px * 0.04);
      t!.needsUpdate = true;
    });
    return t;
  }, [text, fg, bg, weight, px, w, h]);
}

/** A text label as a plane. Ground labels lie flat; wall labels stand up. */
export function Label({ text, at, width, rotY = 0, flat = false, ...opts }: {
  text: string; at: V3; width: number; rotY?: number; flat?: boolean; color?: string; bg?: string; weight?: number;
}) {
  const tex = useTextTexture(text, opts);
  const aspect = 4; // canvas is 512x128
  return (
    <mesh position={at} rotation={flat ? [-Math.PI / 2, 0, rotY] : [0, rotY, 0]}>
      <planeGeometry args={[width, width / aspect]} />
      <meshBasicMaterial map={tex} transparent depthWrite={false} toneMapped={false} />
    </mesh>
  );
}

/** heading_rad (0 = east, +pi/2 = south) to a three.js Y rotation for models built facing +x. */
export const headingToRotY = (h: number) => -h;
