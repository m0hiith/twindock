// Orthographic isometric camera: ~35° elevation, 45° yaw; rotation only in 90° steps (map
// controls), zoom 0.6x–2x of fit-to-site, pan by dragging. All motion is eased.
import { useFrame, useThree } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import type { Layout } from "../layout";
import { useView, useWorld } from "../store/world";
import { ZOOM_MAX, ZOOM_MIN } from "../store/world";
import { cameraState, ELEVATION } from "./camera";
import { dragState } from "./dragState";

const DIST = 200;
/** Metres across the screen at 1x for each site (the warehouse and yard; the factory and the whole east side of the campus). */
const SITE_VIEW: Record<string, [number, number]> = { "WH-01": [78, 52], "FAC-01": [140, 90] };

/** Middle of every site's bounds, for the overview camera. */
function campusCentre(sites: { bounds: { x: [number, number]; z: [number, number] } }[]): [number, number] | undefined {
  if (!sites.length) return undefined;
  const x = sites.flatMap((s) => s.bounds.x), z = sites.flatMap((s) => s.bounds.z);
  return [(Math.min(...x) + Math.max(...x)) / 2, (Math.min(...z) + Math.max(...z)) / 2];
}
const HOME = new THREE.Vector3(32, 0, 27); // WH-01: between the warehouse and the yard
const DRAG_PX = 4; // movement before a press counts as a drag rather than a click

export function CameraRig({ layout }: { layout: Layout }) {
  const { camera, size, gl } = useThree();
  const rotation = useView((s) => s.rotation);
  const zoom = useView((s) => s.zoom);
  const homeNonce = useView((s) => s.homeNonce);
  const focus = useView((s) => s.focus);
  const siteId = useView((s) => s.site);
  const overview = siteId === "ALL"; // the monitoring centre looks at every site at once
  const sites = useWorld((s) => s.sites);
  const siteHome = useMemo(() => (overview ? campusCentre(sites) : sites.find((x) => x.id === siteId)?.home), [overview, sites, siteId]);
  const home = siteHome ? new THREE.Vector3(siteHome[0], 0, siteHome[1]) : HOME;

  const target = useRef(home.clone());
  const goal = useRef(home.clone());
  const zoomShown = useRef(zoom);

  // eslint-disable-next-line react-hooks/exhaustive-deps -- home is recomputed every render; nonce/site drive it
  useEffect(() => { goal.current.copy(home); }, [homeNonce, siteId, siteHome?.[0], siteHome?.[1]]);
  useEffect(() => { if (focus) goal.current.set(focus.x, 0, focus.z); }, [focus]);

  // Pan by drag, zoom by wheel.
  useEffect(() => {
    const el = gl.domElement;
    let down: { x: number; y: number } | null = null;
    let last = { x: 0, y: 0 };
    const onDown = (e: PointerEvent) => {
      down = { x: e.clientX, y: e.clientY };
      last = { ...down };
      dragState.moved = false;
    };
    const onMove = (e: PointerEvent) => {
      if (!down) return;
      if (!dragState.moved && Math.hypot(e.clientX - down.x, e.clientY - down.y) < DRAG_PX) return;
      dragState.moved = true;
      el.style.cursor = "grabbing";
      const dx = e.clientX - last.x, dy = e.clientY - last.y;
      last = { x: e.clientX, y: e.clientY };
      const ppm = (camera as THREE.OrthographicCamera).zoom; // pixels per metre
      const yaw = cameraState.yaw;
      const right = new THREE.Vector3(Math.sin(yaw), 0, -Math.cos(yaw));
      const away = new THREE.Vector3(-Math.cos(yaw), 0, -Math.sin(yaw));
      // Screen-vertical maps to ground distance stretched by 1/sin(elevation).
      const move = right.multiplyScalar(-dx / ppm).add(away.multiplyScalar(dy / ppm / Math.sin(ELEVATION)));
      goal.current.add(move);
      target.current.add(move);
    };
    const onUp = () => {
      down = null;
      el.style.cursor = "";
      // Let this pointerup's click handlers see the drag flag, then clear it.
      setTimeout(() => { dragState.moved = false; }, 0);
    };
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      useView.getState().zoomBy(Math.exp(-e.deltaY * 0.0015));
    };
    el.addEventListener("pointerdown", onDown);
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => {
      el.removeEventListener("pointerdown", onDown);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      el.removeEventListener("wheel", onWheel);
    };
  }, [camera, gl]);

  useFrame((_, dt) => {
    const cam = camera as THREE.OrthographicCamera;
    const k = 1 - Math.exp(-8 * Math.min(dt, 0.1));
    const wantYaw = Math.PI / 4 + (rotation * Math.PI) / 2;
    cameraState.yaw += (wantYaw - cameraState.yaw) * k;

    const { x, z } = layout.bounds;
    goal.current.x = THREE.MathUtils.clamp(goal.current.x, x[0], x[1]);
    goal.current.z = THREE.MathUtils.clamp(goal.current.z, z[0], z[1]);
    target.current.lerp(goal.current, k);

    zoomShown.current += (THREE.MathUtils.clamp(zoom, ZOOM_MIN, ZOOM_MAX) - zoomShown.current) * k;
    // 1x = the warehouse and yard fill the view (~78 m across the diagonal).
    const [vw, vh] = overview ? [250, 135] : (SITE_VIEW[siteId] ?? [78, 52]);
    const fit = Math.min(size.width / vw, size.height / vh);
    const ppm = fit * zoomShown.current;
    if (Math.abs(cam.zoom - ppm) > 1e-4) {
      cam.zoom = ppm;
      cam.updateProjectionMatrix();
    }
    const yaw = cameraState.yaw, c = Math.cos(ELEVATION);
    cam.position.set(target.current.x + Math.cos(yaw) * c * DIST, Math.sin(ELEVATION) * DIST, target.current.z + Math.sin(yaw) * c * DIST);
    cam.lookAt(target.current);
  });
  return null;
}
