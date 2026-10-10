// Which site a point belongs to (sites share one metre grid; their bounds don't overlap).
import type { Site } from "./contract";

export function siteAt(sites: Site[], x: number, z: number): string | undefined {
  return sites.find((s) => x >= s.bounds.x[0] && x <= s.bounds.x[1] && z >= s.bounds.z[0] && z <= s.bounds.z[1])?.id;
}
