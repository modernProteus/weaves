#!/usr/bin/env node
// CQ build: nodes/*.json -> dist/
// Zero dependencies. Node 18+.  Run: node build.mjs

import { readFileSync, writeFileSync, readdirSync, mkdirSync, rmSync, cpSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { KINDS, MODES, modeOf, validate, lineage, volleys } from "./schema.mjs";

const root = dirname(fileURLToPath(import.meta.url));
const cfg = JSON.parse(readFileSync(join(root, "weaves.config.json"), "utf8"));
const BASE = cfg.baseUrl.replace(/\/+$/, "");
const T = p => readFileSync(join(root, "templates", p), "utf8");

const esc = s => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const attr = s => esc(s).replace(/"/g, "&quot;");
const fill = (t, m) => t.replace(/\{\{(\w+)\}\}/g, (x, k) => (k in m ? m[k] : x));
// people entries may be a plain name or { name, contact }
const person = k => { const v = cfg.people?.[k]; return typeof v === "string" ? { name: v } : (v || {}); };
const who = k => person(k).name || k || "—";
// replies go to whoever authored the node, not to a single global address
const contactOf = k => person(k).contact || cfg.replyTo || "";
const days = iso => Math.floor((Date.now() - new Date(iso + "T00:00:00Z")) / 864e5);
const age = n => n <= 0 ? "today" : n === 1 ? "1 day" : n < 30 ? `${n} days`
  : n < 60 ? "1 month" : `${Math.floor(n / 30)} months`;

/* ── load & validate ──────────────────────────────────────── */

const dir = join(root, "nodes");
const nodes = readdirSync(dir).filter(f => f.endsWith(".json")).map(f => {
  const n = JSON.parse(readFileSync(join(dir, f), "utf8"));
  n.id ||= f.replace(/\.json$/, "");
  n.kind ||= "thread";
  n.parent ??= null;
  n.status ||= "open";
  n.reads ||= [];
  n.chips ||= [];
  n.exchange ||= [];
  n.log ||= [];
  return n;
});

// Drafts build nothing and appear nowhere. Somewhere to hold a half-formed branch.
const drafts = nodes.filter(n => n.status === "draft").length;
for (let i = nodes.length - 1; i >= 0; i--) if (nodes[i].status === "draft") nodes.splice(i, 1);

const byId = new Map(nodes.map(n => [n.id, n]));

const problems = [];
for (const n of nodes) for (const e of validate(n, byId)) problems.push(`  ${n.id}: ${e}`);

for (const n of nodes) {
  const seen = new Set();
  let c = n;
  while (c?.parent) {
    if (seen.has(c.id)) { problems.push(`  ${n.id}: lineage loops back on itself.`); break; }
    seen.add(c.id);
    c = byId.get(c.parent);
  }
}

if (problems.length) {
  console.error("\nCan't build. Each record has to satisfy its own mode:\n");
  console.error(problems.join("\n"));
  console.error("\nSee schema.mjs for the full rules and why each one is there.\n");
  process.exit(1);
}

nodes.sort((a, b) => String(b.created).localeCompare(String(a.created)));

const childrenOf = id => nodes.filter(n => n.parent === id)
  .sort((a, b) => String(a.created).localeCompare(String(b.created)));

/* ── pieces ───────────────────────────────────────────────── */

const KC = { thread: "k-thread", workbench: "k-workbench", bookshelf: "k-bookshelf" };

// Lineage spine: one mark per ancestor, current one filled.
function spine(node, { mini = false } = {}) {
  const chain = lineage(node, byId);
  const marks = chain.map((n, i) =>
    `<i class="mark ${KC[n.kind]}${i === chain.length - 1 ? " here" : ""}" title="${attr(KINDS[n.kind].label)}"></i>`
  ).join(`<span class="link" aria-hidden="true"></span>`);

  if (mini) return `<span class="spine mini">${marks}</span>`;

  const v = volleys(chain);
  const m = MODES[modeOf(node)];
  return `<div class="spine" aria-label="depth ${chain.length}">${marks}` +
    `<span class="spine-label">${esc(m.label)} · ${esc(m.hint)}` +
    (v ? ` · ${v} volley${v === 1 ? "" : "s"}` : "") + `</span></div>`;
}

const readBlock = r => `<a class="read" href="${attr(r.url || "#")}" target="_blank" rel="noopener">
  <span class="read-title">${esc(r.title || "Untitled")}</span>
  <span class="read-meta">
    ${r.source ? `<span>${esc(r.source)}</span><span>·</span>` : ""}
    <span>${esc(r.time || "")}</span>
    <span class="arrow" aria-hidden="true">&#8594;</span>
  </span>
  ${r.note ? `<span class="read-note">${esc(r.note)}</span>` : ""}
</a>`;

function inspirationBlock(n) {
  const i = n.inspiration;
  if (!i?.what) return "";
  const inner = `<span class="insp-kind">${esc(i.kind || "source")}</span>${esc(i.what)}`;
  return `<p class="insp"><span class="insp-lead">Sparked by</span>${i.url
    ? `<a href="${attr(i.url)}" target="_blank" rel="noopener">${inner}</a>` : inner}</p>`;
}

function exchangeBlock(n) {
  if (!n.exchange.length) return "";
  return `<p class="label">Handed across</p><ul class="xch">` + n.exchange.map(x => {
    const counted = x.optionsIn != null && x.optionsOut != null;
    const wide = counted && x.optionsOut >= x.optionsIn;
    return `<li>
      <span class="xch-kind">${esc(x.kind || "note")}</span>
      <span class="xch-what">${esc(x.what)}</span>
      ${counted ? `<span class="xch-count${wide ? " wide" : ""}">${x.optionsIn} &#8594; ${x.optionsOut} options${wide ? " · didn't narrow" : ""}</span>` : ""}
    </li>`;
  }).join("") + `</ul>`;
}

function childrenBlock(n) {
  const kids = childrenOf(n.id);
  if (!kids.length) return "";
  return `<p class="label">Branches</p><ul class="rows">${kids.map(k => row(k, { flat: true })).join("")}</ul>`;
}

const parentBlock = n => n.parent
  ? `<p class="from-parent"><a href="${BASE}/n/${n.parent}/">&#8593; ${esc(byId.get(n.parent).title)}</a></p>` : "";

/* ── page body ────────────────────────────────────────────── */

function body(n) {
  const mode = modeOf(n);
  const isThread = n.kind === "thread";
  const P = [spine(n), parentBlock(n)];

  P.push(`<div class="titleblock"><h1>${esc(n.title)}</h1>${n.why ? `<p class="why">${esc(n.why)}</p>` : ""}</div>`);

  if (n.reads.length) {
    P.push(`<hr class="rule">`);
    P.push(`<p class="label">${mode === "broaden" ? `The slate · ${n.reads.length} reads` : "The read"}</p>`);
    if (n.slateNote) P.push(`<p class="slate-note">${esc(n.slateNote)}</p>`);
    P.push(n.reads.map(readBlock).join(""));
    P.push(inspirationBlock(n));
  }

  if (n.hook) P.push(`<p class="label">The question</p><p class="hook">${esc(n.hook)}</p>`);

  if (n.kind === "workbench")
    P.push(`<hr class="rule"><p class="label">The action</p><p class="hook">${esc(n.action)}</p>`);

  if (n.kind === "bookshelf") {
    P.push(`<hr class="rule"><p class="label">Held open</p><p class="hook">${esc(n.question)}</p>`);
    P.push(`<p class="label">If the answer never comes</p><p class="fallback">${esc(n.fallback)}</p>`);
  }

  if (n.chips.length) {
    P.push(`<hr class="rule"><p class="label">Flagged going in</p>`);
    if (n.flagNote) P.push(`<p class="flag-note">${esc(n.flagNote)}</p>`);
    P.push(`<ul class="chips">${n.chips.map(c => `<li>${esc(c)}</li>`).join("")}</ul>`);
  }

  const x = exchangeBlock(n); if (x) P.push(`<hr class="rule">${x}`);
  const c = childrenBlock(n); if (c) P.push(`<hr class="rule">${c}`);

  if (isThread) P.push(`<hr class="rule"><p class="label">No reply needed</p>
    <div class="replies" id="replies" data-title="${attr(n.title)}" data-reply-to="${attr(contactOf(n.from))}">
      <a class="reply warm" data-msg="bite">Bite</a>
      <a class="reply" data-msg="park it">Park it</a>
      <a class="reply" data-msg="pass">Pass</a>
    </div>
    <p class="said" id="said" role="status"></p>`);

  P.push(`<footer>
    <a class="backlink" href="${BASE}/">&#8592; All threads</a>
    <span>${esc(KINDS[n.kind].label)} &middot; ${esc(who(n.from))} &middot; ${esc(n.created)}${isThread ? " &middot; nothing owed" : ""}</span>
  </footer>`);

  return P.join("\n");
}

/* ── index: a forest ──────────────────────────────────────── */

function row(n, { flat = false } = {}) {
  const d = days(n.created);
  const stale = n.kind === "thread" && n.status === "open" && d > (cfg.staleAfterDays ?? 90);
  const kids = flat ? [] : childrenOf(n.id);
  const v = volleys(lineage(n, byId));

  return `<li>
    <a class="row" href="${BASE}/n/${n.id}/">
      ${spine(n, { mini: true })}
      <span>
        <span class="row-title">${esc(n.title)}</span>
        ${(n.hook || n.action || n.question) ? `<p class="row-hook">${esc(n.hook || n.action || n.question)}</p>` : ""}
        <span class="row-meta">
          <span class="tag ${KC[n.kind]}">${esc(MODES[modeOf(n)].label)}</span>
          <span>${esc(who(n.from))}</span>
          <span class="${stale ? "stale" : ""}">${age(d)}${stale ? " · stale" : ""}</span>
          ${v ? `<span>${v} volley${v === 1 ? "" : "s"}</span>` : ""}
        </span>
      </span>
    </a>
    ${kids.length ? `<ul class="rows nested">${kids.map(k => row(k)).join("")}</ul>` : ""}
  </li>`;
}

const roots = nodes.filter(n => !n.parent);
const openRoots = roots.filter(n => n.status === "open").length;

/* ── emit ─────────────────────────────────────────────────── */

const out = join(root, "dist");
rmSync(out, { recursive: true, force: true });
mkdirSync(out, { recursive: true });
for (const f of ["cq.css", "cq.js"]) cpSync(join(root, "templates", f), join(out, f));
// Only claim an image if one actually exists. A 404 og:image degrades the card
// in some clients; omitting it gives a clean text preview instead.
//
// Shape decides the layout the client renders. A square reads as a compact card
// (icon left, title and question right, text as the focus). A wide one forces the
// big banner-on-top form. Read it from the PNG header rather than hardcoding.
const cardPath = join(root, "assets", "card.png");
const hasCard = existsSync(cardPath);
if (hasCard) cpSync(cardPath, join(out, "card.png"));

function pngSize(p) {
  const b = readFileSync(p);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

let OG_IMAGE = `<meta name="twitter:card" content="summary">`;
if (hasCard) {
  const { w, h } = pngSize(cardPath);
  const wide = w / h > 1.4;
  OG_IMAGE = [
    `<meta property="og:image" content="${BASE}/card.png">`,
    `<meta property="og:image:width" content="${w}">`,
    `<meta property="og:image:height" content="${h}">`,
    `<meta property="og:image:alt" content="A single thread coiling inward around a question">`,
    `<meta name="twitter:card" content="${wide ? "summary_large_image" : "summary"}">`
  ].join("\n");
  console.log(`card.png ${w}x${h} -> ${wide ? "large banner" : "compact card"}`);
}

// Experiment: iMessage documents og:video with MP4 as the path to motion,
// since GIFs render as a first frame only. Support is inconsistent, so og:image
// stays as the fallback and every client that ignores this still gets a card.
const videoPath = join(root, "assets", "spark.mp4");
const hasVideo = existsSync(videoPath);
if (hasVideo) cpSync(videoPath, join(out, "spark.mp4"));

let OG_VIDEO = "";
if (hasVideo) {
  const vw = cfg.video?.width ?? 1200;
  const vh = cfg.video?.height ?? 1200;
  OG_VIDEO = "\n" + [
    `<meta property="og:video" content="${BASE}/spark.mp4">`,
    `<meta property="og:video:secure_url" content="${BASE}/spark.mp4">`,
    `<meta property="og:video:type" content="video/mp4">`,
    `<meta property="og:video:width" content="${vw}">`,
    `<meta property="og:video:height" content="${vh}">`
  ].join("\n");
  console.log(`spark.mp4 present -> og:video ${vw}x${vh}`);
}

const shell = T("page.html");

for (const n of nodes) {
  mkdirSync(join(out, "n", n.id), { recursive: true });
  writeFileSync(join(out, "n", n.id, "index.html"), fill(shell, {
    BASE, OG_IMAGE, OG_VIDEO, URL: `${BASE}/n/${n.id}/`,
    TITLE_ATTR: attr(n.title),
    DESC_ATTR: attr(n.hook || n.action || n.question || n.why || ""),
    KIND_LABEL: attr(KINDS[n.kind].label),
    CLASS: "",
    BODY: body(n)
  }));
}

writeFileSync(join(out, "index.html"), fill(shell, {
  BASE, OG_IMAGE, OG_VIDEO, URL: `${BASE}/`,
  TITLE_ATTR: "Threads",
  DESC_ATTR: attr(`${openRoots} open. Nothing owed.`),
  KIND_LABEL: "Weaves",
  CLASS: " wide",
  BODY: `<div class="masthead">
      <h1>Threads</h1>
      <span class="count">${openRoots} open · ${nodes.length} nodes</span>
    </div>
    <p class="sub">Every inquiry enters the same way: one read, one question. What happens after is emergent.</p>
    <a class="new" href="https://github.com/${cfg.repo}/issues/new?template=thread.yml">+ New thread</a>
    <div class="legend">
      <span><i class="mark k-thread here"></i>thread</span>
      <span><i class="mark k-workbench here"></i>workbench · building</span>
      <span><i class="mark k-bookshelf here"></i>bookshelf · held open</span>
    </div>
    ${roots.length ? `<ul class="rows">${roots.map(n => row(n)).join("")}</ul>`
      : `<p class="empty">Nothing queued. That's a fine state to be in.</p>`}
    <footer><span>Cap 5 open &middot; stale after ${cfg.staleAfterDays ?? 90} days &middot; built ${new Date().toISOString().slice(0, 10)}</span></footer>`
}));

console.log(`built ${nodes.length} node(s), ${roots.length} root(s)${drafts ? `, ${drafts} draft held back` : ""} -> dist/`);
for (const n of nodes) console.log(`  ${modeOf(n).padEnd(8)} ${BASE}/n/${n.id}/`);
