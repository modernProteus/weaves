# Weaves

spark · thread · workbench · bookshelf

Every inquiry enters the same way: one read, one question. What happens after is emergent.

```
  thread ──▶ broaden ──┬──▶ BENCH ◀──┐
   offer     pooled    │       │      │  volley
                       └──▶ SHELF ◀───┘  (emergent)
```

Constrained entry, free interior. Structure is cheapest at the boundary and most
annoying in the middle.

## Modes

| mode | what it's for | gate |
|---|---|---|
| **thread** | An offer. One read, one question. | a read and a question |
| **broaden** | Strands pooled so they pull against each other. | 2+ reads **and** a note on the tension |
| **workbench** | Building. | a nameable action |
| **bookshelf** | A question held under tension. Returns a constraint, not an answer. | the question **and** what you'd build without the answer |

Mode is **derived, never stored.** One read is a thread; several is a broadening.
Add a second read to a thread and it becomes a broadening on its own.

Threads are roots. Workbench and bookshelf are always branches, and either can spawn either,
so a standalone bookshelf exploration that grows a workbench to support it is a normal shape.
"Standalone" describes a branch, not a root.

## The gates are enforced by the build

`node build.mjs` fails if a record doesn't satisfy its own mode, and the error quotes
the reason. Bookshelf without a fallback:

```
  when-fusion-is-right: missing "fallback" — You may only send a question up if you
  can also say what you'd build if the answer never came. This is the rule that stops
  the Bookshelf becoming an escape hatch from a hard build decision. Deferral dressed as
  depth is very hard to catch from the inside.
```

Reasons live in `schema.mjs` next to the rules. Change a rule, change its reason.

## Why there's a build step

Apple's link-preview crawler requires HTTPS, reads raw HTML, and won't run JavaScript.
One page serving many records from a query string would show an identical preview for
every one. So each node gets a static page with its own `og:` tags baked in.

Preview card: **title** = the title, **description** = the question.

## Setup, about ten minutes

1. Push this to a repo.
2. Settings → Pages → Source: **GitHub Actions**
3. Settings → Actions → General → Workflow permissions: **Read and write**
4. Edit `weaves.config.json`: `baseUrl`, `repo`, and optionally `replyTo` (phone or email —
   turns the reply buttons into prefilled messages; empty means copy to clipboard).

## Adding something

**Phone.** Issues → New issue → *New thread* or *Branch*. Three required fields on a
thread; every field says what it wants and why it's required. A bot writes the JSON,
comments with the link to send, and closes the issue. If a gate fails it comments with
the reason and leaves the issue open.

**Laptop.** Drop a file in `nodes/`, push.

## Fields

| field | notes |
|---|---|
| `kind` | `thread` \| `workbench` \| `bookshelf` |
| `parent` | lineage. one, immutable, set at creation. `null` for threads. |
| `reads[]` | `{title, source, time, url, note}`. Count drives the mode. |
| `slateNote` | required once there's more than one read: what's the tension |
| `inspiration` | `{kind, what, url?}` — where it came from, kept out of `reads` |
| `exchange[]` | `{date, to, kind, what, optionsIn, optionsOut}` |
| `log[]` | append only, never edited |

### Why `inspiration` isn't a read

Because `reads[]` cardinality decides the mode. Drop a reel in there next to the paper
and a thread silently reads as a broadening. Beyond that they do different jobs:
**`why` is the pitch, `inspiration` is the receipt.** One argues, the other discloses.

### The option count

`optionsIn` and `optionsOut` on an exchange record. The volley should **narrow.** A
bookshelf trip that returns more open options than went up produced material, not a
constraint. The index marks it. Two integers, and it will catch the thing.

## Local

```sh
node build.mjs
npx serve dist
```

## Conventions this encodes

- Cap 5 open threads. Shown, not enforced — a tool that refuses your input turns a
  convention you chose into a rule imposed on you.
- Stale after 90 days, flagged on the index.
- No read receipts. Ignoring a thread has to stay free.
- Threads close their issue immediately. An open comment thread is an obligation, and
  that's what a branch is for.
