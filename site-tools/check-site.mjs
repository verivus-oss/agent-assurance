import { lstatSync, readFileSync, readdirSync, statSync } from "node:fs";
import { extname, join } from "node:path";

const root = new URL("../site/", import.meta.url).pathname;
const required = [
  "index.html",
  "spec/index.html",
  "profiles/index.html",
  "validators/index.html",
  "compare/index.html",
  "agent-readiness/index.html",
  "assets/favicon.ico",
  "assets/favicon.svg",
  "assets/apple-touch-icon.png",
  "assets/og-image.png",
  "llms.txt",
  "sitemap.xml",
  "sitemap.md",
  "robots.txt",
  "AGENTS.md",
  "ab02de421738fed7233351db2d3ab5f4a4fbddb8050cc6c977b2fc940b8c8a68.txt",
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

export function hasProviderTagline(content) {
  const providerName = ["Clau", "de"].join("");
  const folded = content.toLowerCase();
  const provider = providerName.toLowerCase();
  return folded.includes(`${provider} code`)
    || folded.includes(`${provider}.ai/code`)
    || folded.includes(`generated with ${provider}`)
    || content.split("\n").some((line) => {
      const lower = line.toLowerCase();
      const trailer = lower.indexOf("co-authored-by:");
      return trailer >= 0 && lower.slice(trailer).includes(provider);
    });
}

const publishedExtensions = new Set([
  ".css", ".html", ".ico", ".json", ".md", ".png", ".svg", ".txt", ".xml",
]);
const publishedExtensionless = new Set(["_headers", "_redirects"]);

export function findUnexpectedPublishedFiles(dir) {
  const found = [];
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    const stat = lstatSync(path);
    if (stat.isDirectory()) found.push(...findUnexpectedPublishedFiles(path));
    else if (!stat.isFile() || !(publishedExtensions.has(extname(name)) || publishedExtensionless.has(name))) {
      found.push(path);
    }
  }
  return found;
}

function walk(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    const stat = lstatSync(path);
    if (stat.isDirectory()) walk(path);
    else if (stat.isFile() && [".html", ".md", ".txt", ".xml", ".json", ".css", ".svg"].some((suffix) => name.endsWith(suffix))) {
      const content = readFileSync(path, "utf8");
      if (hasProviderTagline(content)) {
        console.error(`provider tagline found in ${path}`);
        ok = false;
      }
    }
  }
}

for (const path of findUnexpectedPublishedFiles(root)) {
  console.error(`unexpected file in published site: ${path}`);
  ok = false;
}
walk(root);
if (!ok) process.exit(1);
console.log("site checks passed");
