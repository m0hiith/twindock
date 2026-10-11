// Displayed camera yaw, written by CameraRig each frame. 0 = camera east of target, +pi/2 = south.
export const cameraState = { yaw: Math.PI / 4 };
export const ELEVATION = (35 * Math.PI) / 180;

/** Level of detail from the camera zoom in pixels per metre, with hysteresis so the model doesn't flicker at a threshold. */
export const LOD_FAR_BELOW = 9;
export const LOD_NEAR_FROM = 16;
export type Lod = "far" | "mid" | "near";
export function lodFor(ppm: number, current: Lod): Lod {
  if (ppm < LOD_FAR_BELOW * (current === "far" ? 1.1 : 1)) return "far";
  return ppm < LOD_NEAR_FROM * (current === "near" ? 0.9 : 1) ? "mid" : "near";
}

/** The ground quadrilateral the camera sees (for the mini-map): top-left, top-right, bottom-right, bottom-left. */
export function viewCorners(target: { x: number; z: number }, yaw: number, ppm: number, width: number, height: number): [number, number][] {
  const rx = Math.sin(yaw), rz = -Math.cos(yaw); // screen right on the ground
  const ax = -Math.cos(yaw), az = -Math.sin(yaw); // screen up on the ground (away from the camera)
  const hw = width / 2 / ppm, hh = height / 2 / (ppm * Math.sin(ELEVATION)); // screen-vertical is stretched by 1/sin(elevation)
  return ([[-1, 1], [1, 1], [1, -1], [-1, -1]] as const).map(([sx, up]) => [target.x + rx * hw * sx + ax * hh * up, target.z + rz * hw * sx + az * hh * up]);
}
