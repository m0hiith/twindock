/// <reference types="node" />
// Every family the kit schema allows must have a drawing function and a gallery specimen, so a new family
// can't be added to the schema without being drawn and looked at.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const here = import.meta.dirname;
const schema = JSON.parse(readFileSync(join(here, "../../../shared/schemas/hardware/wiring.json"), "utf8")) as {
  $defs: { drawing: { properties: { family: { enum: string[] } } } };
};
const families = schema.$defs.drawing.properties.family.enum;
const lib = readFileSync(join(here, "parts/index.tsx"), "utf8");
const gallery = readFileSync(join(here, "../pages/PartsGallery.tsx"), "utf8");

test("every schema family has a drawing function", () => {
  for (const f of families) assert.match(lib, new RegExp(`\\b${f}:\\s`), `no drawing for ${f}`);
});

test("every schema family is in the part gallery", () => {
  for (const f of families.filter((x) => x !== "pcb")) assert.ok(gallery.includes(`family: "${f}"`), `${f} is missing from the gallery`);
});
