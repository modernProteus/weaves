# Handoff — repo setup and deploy

A static site generator for a shared conversation queue between two people.
Everything builds and passes locally. What's left is the parts that need a terminal
and a live URL, which is why it's coming to you.

Read `README.md` first for what the thing is.

---

## The work

### 1. Publish

- Public GitHub repo named **`weaves`**
- `git init`, commit, push to `main`
- Settings → Pages → Source: **GitHub Actions**
- Settings → Actions → General → Workflow permissions: **Read and write**
  (without this the issue bot can't commit, and it fails silently-ish)

### 2. Point the config at reality

`weaves.config.json` ships with placeholders:

```json
"baseUrl": "https://YOURNAME.github.io/weaves",
"repo":    "YOURNAME/weaves"
```

Replace both with the real values, rebuild, confirm the printed URLs match what
Pages actually serves. Ask before setting `replyTo` — that's a personal phone
number or email and the owner should supply it, not you.

### 3. Watch the deploy and fix what breaks

`.github/workflows/pages.yml` runs `node build.mjs` and deploys `dist/`.
Zero dependencies, Node 20. If it fails, fix it.

### 4. Verify the thing this was all built for

The entire architecture exists because Apple's link-preview crawler reads raw HTML
and will not execute JavaScript. So confirm the tags survive the round trip:

```sh
curl -s https://YOURNAME.github.io/weaves/n/identity-fusion/ | grep 'og:'
```

Expect `og:title` = the node title and `og:description` = the question, present in
the raw response. If they're missing or identical across nodes, something regressed
and it's the most important bug in the repo.

**What you can't verify and shouldn't try:** the actual iMessage rendering. Tell the
owner to text themselves the link. If it comes through as a bare URL it's usually
`baseUrl` still wrong, or iOS caching its first fetch, which it does aggressively.

### 5. Exercise the issue path

Open a test issue with the **New thread** template. Confirm the bot writes
`nodes/<id>.json`, comments the link, and closes the issue. Then open one that
deliberately fails a gate — a **Branch** of kind `bookshelf` with no fallback — and
confirm it comments the reason and leaves the issue open. Delete both test nodes
and their commits afterward.

---

## Conventions to hold to

**Zero runtime dependencies.** `build.mjs` and `schema.mjs` use nothing but Node
stdlib. Keep it that way. If something seems to need a package, say so rather than
adding one.

**Rules and their reasons live together.** Every requirement in `schema.mjs` carries
a `why` string, and build errors quote it verbatim so a failure explains itself.
Adding a rule means writing its reason. This is the point of the file, not decoration.

**Mode is derived, never stored.** One read is a `thread`; two or more is a
`broaden`. Don't add a mode field.

**Gates are real.** A `workbench` needs an action. A `bookshelf` needs a question
*and* a statement of what you'd build if the answer never came. Don't soften these
to make a test pass — fix the test data instead.

---

## Do not touch

**The `spark` / `thread` relationship.** Currently `spark` is the verb (what sending
a thread does) and `thread` is the record. The owner has deliberately left this
unsettled to see what he and his collaborator actually say out loud. If you see an
inconsistency here, leave it and mention it.

**`nodes/when-fusion-is-right.json` is `status: "draft"` on purpose.** Drafts build
nothing and appear nowhere. It's held back so it doesn't pre-frame a question the
two of them should arrive at themselves. Don't publish it, don't delete it.

**The 5-open cap is displayed, not enforced.** Deliberate. A tool that refuses your
input turns a convention you chose into a rule imposed on you.

**No read receipts, ever.** Ignoring a thread has to stay free. Don't add analytics.

---

## Nice to have, only if the above is done and green

- `assets/card.png` at 1200×630 becomes the shared `og:image`. There isn't one yet;
  without it iMessage renders a clean text card, which is arguably better than a
  generic image. Don't generate one without asking.
- A local preview script (`npx serve dist`) wired into `package.json`.
