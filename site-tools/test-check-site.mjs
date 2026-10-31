import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { hasProviderTagline, findUnexpectedPublishedFiles } from "./check-site.mjs";

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
  writeFileSync(join(temp, "_headers"), "public site headers");
  writeFileSync(join(temp, "_redirects"), "public site redirects");
  assert.deepEqual(findUnexpectedPublishedFiles(temp), []);
  const unexpected = [
    join(temp, "assets", "_headers"),
    join(temp, "assets", "_redirects"),
    join(temp, "assets", "private-test.mjs"),
    join(temp, "assets", "private-test.mts"),
    join(temp, "assets", "private-test.rb"),
    join(temp, "assets", "private-test"),
    join(temp, "assets", "shortcut.md"),
  ];
  for (const path of unexpected.slice(0, -1)) writeFileSync(path, "private helper\n");
  symlinkSync("readme.txt", unexpected.at(-1));
  assert.deepEqual(findUnexpectedPublishedFiles(temp).sort(), unexpected.sort());
} finally {
  rmSync(temp, { recursive: true, force: true });
}
console.log(`site tagline boundaries: ${accepted.length} accepted, ${rejected.length} rejected`);
