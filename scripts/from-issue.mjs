// GitHub issue-form body -> nodes/<id>.json
// Env: ISSUE_BODY, ISSUE_TITLE, ISSUE_LABELS

import { writeFileSync, existsSync, readdirSync, readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { validate } from "../schema.mjs";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const dir = join(root, "nodes");

// Issue forms render as:  ### Label\n\nvalue
const fields = {};
for (const block of (process.env.ISSUE_BODY || "").split(/^### /m).slice(1)) {
  const nl = block.indexOf("\n");
  const label = block.slice(0, nl).trim().toLowerCase();
  const value = block.slice(nl).trim();
  fields[label] = /^_no response_$/i.test(value) ? "" : value;
}
const f = k => (fields[k] || "").trim();

const isBranch = (process.env.ISSUE_LABELS || "").includes("branch");
const title = f("title") ||
  (process.env.ISSUE_TITLE || "").replace(/^(Thread|Branch|Spark):\s*/i, "").trim();

if (!title) { console.error("::error::No title."); process.exit(1); }

const slugify = s => s.toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "")
  .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60);

let id = slugify(title), n = 2;
while (existsSync(join(dir, `${id}.json`))) id = `${slugify(title)}-${n++}`;

const list = s => s.split(",").map(x => x.trim()).filter(Boolean);

const node = {
  id,
  kind: isBranch ? (f("workbench or bookshelf") || "workbench") : "thread",
  parent: isBranch ? f("comes off which node") || null : null,
  title,
  from: f("from") || "nick",
  created: new Date().toISOString().slice(0, 10),
  status: "open",
  why: f("why this"),
  chips: list(f("trap terms")),
  flagNote: f("note on the traps"),
  reads: [],
  exchange: [],
  log: []
};

if (isBranch) {
  if (node.kind === "workbench") node.action = f("workbench only — the action");
  if (node.kind === "bookshelf") {
    node.question = f("bookshelf only — the question held open");
    node.fallback = f("bookshelf only — what you'd build if the answer never came");
  }
} else {
  node.hook = f("the question");
  const url = f("link to the read");
  if (url) node.reads.push({
    title: f("what the read is called") || title,
    source: f("source line"),
    time: f("how long it takes") || "~10 min",
    url
  });
  const what = f("sparked by");
  if (what) node.inspiration = {
    kind: f("sparked by — what kind") || "other",
    what,
    url: f("sparked by — link") || undefined
  };
}

// validate against the same rules the build uses, so failures explain themselves
const byId = new Map(readdirSync(dir).filter(x => x.endsWith(".json"))
  .map(x => { const j = JSON.parse(readFileSync(join(dir, x), "utf8")); return [j.id || x.replace(/\.json$/, ""), j]; }));
byId.set(node.id, node);

const errs = validate(node, byId);
if (errs.length) {
  console.error("::error::" + errs.join(" | "));
  writeFileSync(join(root, ".cq-errors"), errs.map(e => `- ${e}`).join("\n"));
  process.exit(2);
}

writeFileSync(join(dir, `${id}.json`), JSON.stringify(node, null, 2) + "\n");
console.log(id);
