import assert from "node:assert/strict";
import { hasProviderTagline } from "./check-site.mjs";

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
console.log(`site tagline boundaries: ${accepted.length} accepted, ${rejected.length} rejected`);
