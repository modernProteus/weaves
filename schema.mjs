// The rules, in one place, with reasons attached.
// Build errors quote the `why` verbatim so a failure explains itself.

export const KINDS = {

  thread: {
    label: "Thread",
    blurb: "An offer. One read, one question. Nothing owed.",
    requires: [
      { field: "title", why: "It's the headline on the preview card and the label in the queue." },
      { field: "hook",  why: "This is the offer. It also becomes the text under the link in Messages, so it's the only thing they see before deciding." },
      { field: "reads", why: "A thread is a read plus a question. Without the read there's nothing to pull on.",
        check: v => Array.isArray(v) && v.length >= 1 }
    ]
  },

  workbench: {
    label: "Workbench",
    blurb: "Work. An action is named and something gets built.",
    requires: [
      { field: "title", why: "It's the label in the queue." },
      { field: "action", why: "The gate into Workbench is a nameable action. \"We should build something\" doesn't clear it; \"we should build a thing that does X\" does. If you can't finish the sentence, you're still broadening." }
    ]
  },

  bookshelf: {
    label: "Bookshelf",
    blurb: "A question held under tension. Returns a constraint, not an answer.",
    requires: [
      { field: "question", why: "The gate into Bookshelf is a question the work can't answer by working harder. Naming it is the check." },
      { field: "fallback", why: "You may only send a question up if you can also say what you'd build if the answer never came. This is the rule that stops the Bookshelf becoming an escape hatch from a hard build decision. Deferral dressed as depth is very hard to catch from the inside." }
    ]
  }
};

// Mode is derived, never stored. One read is an offer; several in tension is a broadening.
export const modeOf = n =>
  n.kind === "thread" ? (n.reads?.length > 1 ? "broaden" : "thread") : n.kind;

export const MODES = {
  thread:  { label: "Thread",  hint: "one strand offered" },
  broaden: { label: "Broaden", hint: "strands pooled, pulling against each other" },
  workbench:   { label: "Workbench",   hint: "building" },
  bookshelf:   { label: "Bookshelf",   hint: "held under tension" }
};

export function validate(node, byId) {
  const spec = KINDS[node.kind];
  const errs = [];

  if (!spec) return [`unknown kind "${node.kind}". Use: thread, workbench, or bookshelf.`];

  for (const r of spec.requires) {
    const v = node[r.field];
    const ok = r.check ? r.check(v) : (typeof v === "string" ? v.trim() : v);
    if (!ok) errs.push(`missing "${r.field}" — ${r.why}`);
  }

  if (node.kind === "thread" && node.parent)
    errs.push(`threads are roots. A thread can't have a parent; use kind "workbench" or "bookshelf" for a branch.`);

  if (node.kind !== "thread" && !node.parent)
    errs.push(`a ${node.kind} is always a branch off something. Set "parent" to the id it came from.`);

  if (node.parent && !byId.has(node.parent))
    errs.push(`parent "${node.parent}" doesn't exist.`);

  // broaden wants tension, not just volume
  if (modeOf(node) === "broaden" && !node.slateNote)
    errs.push(`missing "slateNote" — with more than one read this is a broadening, and the point is that the reads pull against each other. Say what the tension is. If they all agree, you have a longer thread, not a broadening.`);

  return errs;
}

export function lineage(node, byId) {
  const chain = [];
  let cur = node, guard = 0;
  while (cur && guard++ < 50) {
    chain.unshift(cur);
    cur = cur.parent ? byId.get(cur.parent) : null;
  }
  return chain;
}

// How many times an inquiry has crossed between building and holding.
export const volleys = chain =>
  chain.filter(n => n.kind !== "thread")
       .reduce((n, x, i, a) => n + (i > 0 && a[i - 1].kind !== x.kind ? 1 : 0), 0);
