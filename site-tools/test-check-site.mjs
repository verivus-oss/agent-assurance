import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { hasProviderTagline, findPublishedExecutables } from "./check-site.mjs";

const accepted = [
  "A provider-neutral assurance guide.",
  "Co-authored-by: A Reader <reader@example.org>",
  "A quoted mention of Claude without a generated-with claim.",
];
const rejected = [
  "Generated with Claude",
  "CLAUDE CODE provided the content",
  "See claude.ai/code for the generator",
  "Co-Authored-By: Claude <author@example.org>",
];
for (const value of accepted) assert.equal(hasProviderTagline(value), false, value);
for (const value of rejected) assert.equal(hasProviderTagline(value), true, value);
const temp = mkdtempSync(join(tmpdir(), "site-source-check-"));
try {
  mkdirSync(join(temp, "assets"));
  writeFileSync(join(temp, "assets", "readme.txt"), "public text");
  assert.deepEqual(findPublishedExecutables(temp), []);
  const source = join(temp, "assets", "private-test.mjs");
  writeFileSync(source, "console.log('private helper');\n");
  assert.deepEqual(findPublishedExecutables(temp), [source]);
} finally {
  rmSync(temp, { recursive: true, force: true });
}
console.log(`site tagline boundaries: ${accepted.length} accepted, ${rejected.length} rejected`);
