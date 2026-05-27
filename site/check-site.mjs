import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const root = new URL(".", import.meta.url).pathname;
const required = [
  "index.html",
  "spec/index.html",
  "profiles/index.html",
  "validators/index.html",
  "compare/index.html",
  "agent-readiness/index.html",
  "llms.txt",
  "sitemap.xml",
  "sitemap.md",
  "robots.txt",
  "AGENTS.md",
  ".well-known/agent.json",
  ".well-known/agent-skills/index.json",
];

let ok = true;
for (const file of required) {
  const path = join(root, file);
  try {
    statSync(path);
  } catch {
    console.error(`missing ${file}`);
    ok = false;
  }
}

function walk(dir) {
  const providerName = ["Clau", "de"].join("");
  const disallowed = [
    new RegExp(`${providerName} Code`, "i"),
    new RegExp(`${providerName.toLowerCase()}\\.ai/code`, "i"),
    new RegExp(`Generated with ${providerName}`, "i"),
    new RegExp(`Co-Authored-By:.*${providerName}`, "i"),
  ];
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    const stat = statSync(path);
    if (stat.isDirectory()) walk(path);
    else if (/\.(html|md|txt|xml|json|css|svg)$/.test(name)) {
      const text = readFileSync(path, "utf8");
      if (disallowed.some((pattern) => pattern.test(text))) {
        console.error(`provider tagline found in ${path}`);
        ok = false;
      }
    }
  }
}

walk(root);
if (!ok) process.exit(1);
console.log("site checks passed");
