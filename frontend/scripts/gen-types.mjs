// Generates src/contract/generated.ts from /shared/schemas (the single message definition).
// Run with: npm run gen:types. Never edit generated.ts by hand.
import { compile } from "json-schema-to-typescript";
import { readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../../shared/schemas");
const load = (p) => JSON.parse(readFileSync(p, "utf8"));
const files = {};
for (const dir of ["mqtt", "ws"]) {
  for (const f of readdirSync(join(root, dir)).filter((f) => f.endsWith(".json"))) files[`${dir}/${f}`] = load(join(root, dir, f));
}

// Inline cross-file $refs ("defs.json#/$defs/x", "../mqtt/gateway_hello.json") into local "#/$defs/..."
// so each output type has one name and the compiler needs no network/file resolver.
function rewrite(node, fromDir, defs) {
  if (Array.isArray(node)) return node.map((n) => rewrite(n, fromDir, defs));
  if (!node || typeof node !== "object") return node;
  const out = {};
  for (const [k, v] of Object.entries(node)) {
    if (k === "$ref" && typeof v === "string" && !v.startsWith("#")) {
      const [file, frag] = v.split("#");
      const key = join(fromDir, file).replace(/\\/g, "/");
      const target = files[key];
      if (!target) throw new Error(`unresolved ${v} from ${fromDir}`);
      if (frag) {
        const name = frag.split("/").pop();
        out[k] = `#/$defs/${name}`;
      } else {
        const name = key.split("/").pop().replace(".json", "");
        defs[name] ??= rewrite({ ...target, $id: undefined, $schema: undefined }, dirname(key), defs);
        out[k] = `#/$defs/${name}`;
      }
    } else if (k !== "$id" && k !== "$schema") {
      out[k] = rewrite(v, fromDir, defs);
    }
  }
  return out;
}

const defs = {};
const wsDefs = files["ws/defs.json"].$defs;
for (const [name, d] of Object.entries(wsDefs)) defs[name] = rewrite(d, "ws", defs);
const combined = { title: "TwinDockContract", type: "object", $defs: defs, properties: {} };
for (const [key, schema] of Object.entries(files)) {
  if (key === "ws/defs.json") continue;
  const name = key.split("/").pop().replace(".json", "");
  defs[name] = rewrite(schema, dirname(key), defs);
  combined.properties[name] = { $ref: `#/$defs/${name}` };
}
for (const [name, d] of Object.entries(defs)) d.title ??= name;
for (const [name, d] of Object.entries(defs)) d.title = name.split("_").map((s) => s[0].toUpperCase() + s.slice(1)).join("");

const ts = await compile(combined, "TwinDockContract", {
  bannerComment: "/* Generated from /shared/schemas by scripts/gen-types.mjs. Do not edit. */",
  additionalProperties: false,
  unreachableDefinitions: true,
  strictIndexSignatures: true,
});
writeFileSync(resolve(dirname(fileURLToPath(import.meta.url)), "../src/contract/generated.ts"), ts);
console.log("wrote src/contract/generated.ts");
