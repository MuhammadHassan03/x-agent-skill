# CEO review of docs/ROADMAP.md

Date: 2026-10-24. Reviewer: gstack `/plan-ceo-review` (v1.91.185.0), run by Claude in this repo.
Mode: SCOPE REDUCTION (your answer to D1). Depth: strategy-only (no implementation design).
Outside voice: disabled (`codex_reviews: disabled` in your gstack config, so no code or plan text left this machine).
Nothing else was changed: no edits to `docs/ROADMAP.md`, no code, no commits. This file is untracked.
Numbers are tagged `[measured: source]` or `[estimated]`.

## Verdict

The principle is the strongest part of the plan and should not change: everything in the repo free and
MIT forever, paid things additive, nothing paid touches X. The risk is sequence, not direction. Three
initiatives are queued for one maintainer while the repo has no validated demand yet: 0 stars, 0 forks,
9 page views and 3 unique visitors in 14 days `[measured: gh api repos/MuhammadHassan03/x-agent-skill/traffic/views, 2026-10-24]`.

Minimum core I would keep: the 2026-11-19 results post and Show HN, then the free weekly algorithm
email as the list-building engine. Everything paid waits for numbers you define now. The cheapest paid
test is a manual voice.md setup offer, which needs no server. The hosted linter is the most expensive
item and the one that conflicts most with the repo's current promise ("upload nothing").

Because you did not answer the per-item deferral questions, **every deferral below is a proposal, not a
decision**. The plan stays exactly as you wrote it until you say otherwise.

## Decision ledger

| ID and owner | Contract and evidence | Current | Proposed | Status | Exact approval and scope |
|---|---|---|---|---|---|
| D1 mode, review | gstack asks the owner to pick a posture | none | SCOPE REDUCTION | approved | Your answer to D1 in this session: review posture only. Approves no change to the plan. |
| D2 hosted linter, paid tier (ROADMAP.md:18-22) | hosting breaks README.md:24-25 "upload nothing"; score AUC 0.449 to 0.500 `[measured: measurement/results.json:16-34]` | in plan, behind ~500 stars | defer to TODOS.md | unresolved | None. The question tool was declined; no answer exists. |
| D3 hook and swipe packs (ROADMAP.md:16) | formula labels did not predict likes `[measured: measurement/results.json:16]`; swipe.py needs hand-collected data | in plan | defer, or keep with an honest "what this is" label | unresolved | None. |
| D4 voice.md setup service (ROADMAP.md:17) | zero infrastructure; first paid test of willingness to pay | in plan | KEEP as a manual first experiment | unresolved | None. |
| D5 briefing paid tier and JSON feed (ROADMAP.md:33-35) | needs a list first; upstream file has ~38 commits since 2026-09-01 `[measured: GitHub API, 2026-10-24]` | in plan, "later" | defer behind a list-size gate you set | unresolved | None. |
| D6 freelance-agent-skill repo (ROADMAP.md:39-43) | splits one maintainer; Upwork data and terms | in plan | defer until repo 1 has traction; keep proposals private for now | unresolved | None. |

Approval readiness: PASS for what exists (only D1 is approved and nothing in the plan changed). The five
proposals are unresolved and listed at the end.

## Step 0

### 0A. Premise challenge (reality rows)

| premise | claim | receipt | verdict |
|---|---|---|---|
| P1 | Everything stays MIT and free forever, including honesty and safety features | LICENSE:1-3, README.md:24-25 | verified as current state |
| P2 | Pro layer starts at roughly 500 stars | repo has 0 stars `[measured: gh repo view, 2026-10-24]` | the trigger is arbitrary; see below |
| P3 | Positioned under Typefully and Tweet Hunter at $9 to $19 a month | competitor prices differ by source (table below) | unverified: sources conflict |
| P4 | A hosted linter's free tier comes "from the MIT tools" | tools are stdlib Python and run locally; no server code exists | feasible, but it is a new product |
| P5 | The tracker "already produces dated weight diffs" | references/ALGO-CHANGELOG.md:5-14, tools/algo_watch.py | verified; first real diff had 3 changes and 0 weights |
| P6 | The email "what to do about it" can be written honestly | README.md measurement: link effect observed, not coded; scorer does not predict likes | partly: advice must carry evidence labels |
| P7 | freelance-agent-skill can have a measurement section | own proposals only; outcome data not described | unverified: n would be small |

`unverified=3` (P3, P6 in part, P7).

- already-done: `git log` shows no pricing, billing, mailing-list or hosted-service code in this repo. Nothing in the roadmap is already built beyond P5.
- surface-check: no new CLI commands or routes are named in the roadmap. No misses.
- binding-decisions: no gstack decision history for this repo yet (LEARNINGS: 0).
- deferred-asks: no linked issue.
- pr-count: not applicable (no code in this review).

### 0B. What already exists

| roadmap need | existing code or asset | reuse |
|---|---|---|
| count, score, humanize, first-reply split | `xcount.py`, `postscore.py --split-link`, `humanize.py`, `detect.py` | direct; they are the hosted linter's logic, all stdlib |
| algorithm diffs | `tools/algo_watch.py`, `references/weights.json`, `ALGO-CHANGELOG.md`, weekly workflow | direct; email body can be generated from the changelog entry |
| voice setup | `templates/voice.md`, `/x-*` skills read `~/.claude/x/voice.md` | direct; the service is a person filling the template |
| landing page | `site/`, GitHub Pages | direct; add a subscribe link, no backend |
| measurement and honesty | `measurement/`, README fine print | the brand asset |

### 0C. Dream state

```
  CURRENT STATE                    THIS PLAN                         12-MONTH IDEAL
  free MIT pack, 0 stars,   --->   Pro layer + briefing +     --->   a trusted, free, measured X-writing
  weekly algo tracker              second repo in parallel            toolkit with a small email list, one
                                                                      paid offer that sells time not
                                                                      data, and a second repo only if
                                                                      the first earned it
```

### Landscape check

Searches were run with the host WebSearch tool, read-only.

| tool | plans seen | note |
|---|---|---|
| Tweet Hunter | Discover $29/mo, Grow $49/mo, Enterprise $200/mo `[estimated: third-party page checked 2026-10-19; direct page not read]` | schedules and posts to X |
| Typefully | sources conflict: Free, Creator $99/yr, Business $20/mo, or an older $10/mo Pro `[estimated: sources disagree]` | schedules and posts to X |
| X algorithm newsletters | none found in a quick search; most coverage is general-marketing blogs | the gap exists but may mean low demand `[estimated]` |

Layer 1: creators pay for scheduling, analytics and AI drafting. Layer 2: coverage of the open-sourced
algorithm is mostly secondary blogs that repeat unverified claims. Layer 3: your edge is the opposite of
the incumbents: a tool that never posts, with receipts. That is a trust product, and trust products are
slow to monetize and cheap to lose.

Two facts to correct in the plan's positioning: your hosted linter would not compete with schedulers on
features (it never posts), so "under Typefully and Tweet Hunter" is a price comparison with products in a
different category; and Typefully's Creator plan at $99/yr is about $8/mo, so $9 to $19 is not clearly
"under" it `[estimated]`.

### 0D and 0G. Minimum core and proposed deferrals (all pending)

Minimum core, the smallest sequence that proves demand:

1. 2026-11-19: results post and Show HN (already planned, out of scope here).
2. Right after: a free weekly email from the changelog, with a single subscribe link on the Pages site.
3. One manual paid test: voice.md setup done for a customer, sold by a payment link. No server.
4. Decide gates from real numbers, then revisit the rest.

Proposals, none approved:

| ID | Proposal | Why | Recommendation |
|---|---|---|---|
| D2 | Defer the paid hosted linter | server, accounts, billing, privacy rewrite; breaks "upload nothing"; free tools already do it locally | defer |
| D3 | Defer hook and swipe packs | your own measurement found hook formulas did not predict likes; selling packs invites the claim you disproved | defer, or keep only with the same honesty framing |
| D4 | Keep the voice.md setup service as the first paid test | no infrastructure, direct signal on willingness to pay | keep |
| D5 | Defer the briefing paid tier and JSON feed | no list yet; the free email must prove readers first | defer behind a gate |
| D6 | Defer freelance-agent-skill as a public repo | second repo doubles maintenance; Upwork content may be client-confidential | defer; keep proposals private |

The 500-star trigger (P2) is a vanity number. Replace it with gates you choose and record in
`docs/ROADMAP.md`, for example: a subscriber count for the email, a count of return visitors or repeat
users, and the number of people who asked for something paid. Pick the numbers yourself; I will not
invent them. If you keep stars as a gate, treat it as a signal of reach, not of willingness to pay.

## Review sections (strategy-only depth)

### Section 1: Architecture

```
  GitHub repo (MIT)            site/ (Pages)           ALGO-CHANGELOG.md
  skills + tools  ----------->  landing + subscribe --> weekly email (3rd-party mailer)
  tools/algo_watch.py (CI)                                      |
        |                                                       v
        v                                               subscriber list = the asset
  references/weights.json                                        |
                                              +------------------+-------------------+
                                              v                                      v
                                   manual voice.md setup                 (deferred) hosted linter,
                                   (payment link, no server)             paid briefing, JSON feed
```

Coupling: the paid layer depends on the list; the list depends on the email; the email depends on the
tracker producing meaningful diffs. A chain with one weak link stops everything. Weak link: the first real
diff had 0 ranking weights `[measured: references/ALGO-CHANGELOG.md:5-14]`. Many weeks may carry only feature
switches. Plan an editorial rule for "nothing changed in the parts that matter this week" so the email
never invents significance.

Single points of failure: one maintainer; one upstream file (xai-org/x-algorithm could move or delete
`param.rs`, which the workflow already handles by opening an issue); one third-party mailer.
Rollback: every item is additive and can be switched off by removing a link, so rollback is minutes for
the email and the service, and large only for the hosted linter once users depend on it.

### Section 2: Error and Rescue map (capability level)

| capability | what can go wrong | rescued today? | user sees | owner must prove |
|---|---|---|---|---|
| weekly email | no meaningful change that week; a wrong claim goes out; unsubscribe fails | no process yet | an empty or misleading email | editorial rule, evidence labels, working unsubscribe |
| email list | a subscriber's data leaks; consent unclear | no mailer chosen | spam or distrust | double opt-in, a privacy note on the site, a mailer with export and delete |
| voice.md service | customer shares private posts or business facts | no process | a breach of trust | a written scope: what is collected, where it lives, when it is deleted |
| payment link | refund, dispute, tax | none | an unhappy customer | a refund promise and tax handling by you or an accountant |
| hosted linter (if built) | customer text stored and exposed; downtime | none | lost data, or the repo's "upload nothing" claim becomes false | threat model before any code |
| JSON feed (if built) | feed sends a bad diff to a customer's tool | none | wrong ranking advice at scale | validation (the 10x guard in `algo_watch.py` is a start) |
| freelance repo | client content in samples; platform terms | none | a terms violation | anonymized samples, no automation |

### Section 3: Security and threat model

| threat | likelihood | impact | mitigated by the plan? |
|---|---|---|---|
| a hosted linter stores customer drafts | High if built | High | no: requires a data-handling design |
| subscriber email list breached | Low to Med | Med | depends on the mailer you pick |
| payment or refund fraud | Low | Low | depends on the payment provider |
| a malicious upstream `param.rs` poisons the email or JSON feed | Low | High for the feed | partly: `algo_watch.py` validates numeric weights and 10x moves, but it does not sanitize names for markdown/HTML; review in the `/cso` step |
| impersonation: "official X" confusion | Med | Med | add a "not affiliated with X" line on the site and in the email |
| Upwork client data in samples | Med | High | no: anonymize first |

The principle "nothing paid ever posts to X or touches X" is a strong security property. Keep it as a
published, testable promise.

### Section 4: Data flow and edge cases

```
  param.rs (upstream) -> algo_watch.py -> validate -> weights.json + ALGO-CHANGELOG.md
                                                     |
        shadow paths:  nil/empty file -> FAILURE issue
                       numeric guard fails -> validation issue, nothing committed
                       0 weight changes -> email still needs an honest "quiet week" body
                                                     v
                                    weekly email (human-written "what to do") -> subscribers
```

Edge cases: a week with 38 commits and no weight change; a week with a weight sign flip (the guard blocks
the commit, so the email would be late); duplicate sends; a subscriber who joins mid-week.

### Section 5: Code quality

No new code is proposed in the roadmap. Implied code: an email generator from `ALGO-CHANGELOG.md` (small,
reuse `algo_watch.py` rendering), and possibly a hosted service (large, new stack, new risk). Keep any
email generator stdlib-only and outside `skills/`, like `tools/algo_watch.py`.

### Section 6: Test review

Tests that would make a 2am Friday send safe: an email generator test with a fixture of a quiet week, a
weight-change week and a validation-failed week; an unsubscribe-link presence test; a "no advice without
an evidence label" check. For the hosted linter, nothing can be assessed until it has a design.

### Section 7: Performance

Not material for the email or the service. For the hosted linter: worst-case input is a 25,000-character
Premium post; the tools handle it in under 0.2 s locally `[measured: earlier timing run, 2026-10-21]`, so
compute is cheap; accounts and storage dominate cost.

### Section 8: Observability

You need to know three things from day one, and none needs analytics on readers: subscriber count and
churn (from the mailer), email send success (mailer logs), and whether the weekly workflow ran
(`algo-watch` Actions history). Do not add tracking pixels to the site; it would contradict the
repo's no-telemetry stance in SECURITY.md.

### Section 9: Deployment and rollout

Order: results post, then email, then manual service, then decide. Each step reversible. Feature flags are
just links. Deploy-time risk: none for the email; for the hosted linter, plan a private beta before any
public paid launch.

### Section 10: Long-term trajectory

Technical debt: low today, high if a hosted service is built. Path dependency: once customers hold saved
data, the "upload nothing" promise is gone for that product and must be stated plainly. Reversibility:
email 5/5, manual service 5/5, JSON feed 3/5 (customers integrate), hosted linter 2/5, second repo 3/5.
The 1-year question: a visitor in 12 months should still see a free, honest, measured toolkit first and an
optional paid layer second. Retrospective on scope: no accepted expansions (mode was reduction).

### Section 11: Design and UX

SKIPPED (no UI scope in the minimum core). If D2 is kept, the hosted linter has UI: run
`/plan-design-review` before building it.

## Required outputs

### NOT in scope

Nothing is declared out of scope by you. These are only proposals (pending): D2, D3, D5, D6 deferral.
Outside this review by your instruction: the 30-day dogfood and the 2026-11-19 results post.

### Dream state delta

After this plan as written, the repo would have three products and no proof any has a user. After the
minimum core, it would have a measured free toolkit, a small list and one real paid signal.

### Failure modes registry

| capability | failure mode | rescued? | test? | user sees | logged? |
|---|---|---|---|---|---|
| weekly email | quiet week padded with fake significance | unknown | no | misleading advice | no |
| weekly email | unsubscribe broken | unknown | no | spam complaint | mailer only |
| tracker to email | validation failure delays the commit | yes (issue opened) | yes (`tests/test_algo_validate.py`) | late email | yes |
| voice.md service | customer data kept too long | unknown | no | privacy breach | no |
| hosted linter | customer drafts stored | unknown | no | broken "upload nothing" promise | no |

**CRITICAL GAP candidates** (RESCUED unknown, TEST no, USER SEES silent or misleading): the quiet-week email
and the hosted-linter storage promise. Both need an owner decision before launch.

### Diagrams

1. System architecture and 2. data flow: Sections 1 and 4.
3. State machine (subscriber): `visitor -> subscribed (double opt-in) -> active -> unsubscribed`; invalid:
   sending to an address that never confirmed. Prevented by the mailer's double opt-in.
4. Error flow: Sections 2 and 4.
5. Deployment sequence: results post, then email, then manual service, then decide.
6. Rollback: remove the subscribe link, pause the mailer, refund open orders. Minutes.

### Stale diagram audit

No ASCII diagrams exist in the files this review touched (`docs/ROADMAP.md` has none).

### Implementation tasks (strategy-only: next actions, no contracts)

- [ ] **T1 (P1, human: ~1h / CC: ~10min)** roadmap: replace the 500-star trigger with gates you choose. Surfaced by: premise P2. Verify: the gates are written in `docs/ROADMAP.md` with numbers you set.
- [ ] **T2 (P1, human: ~2h / CC: ~20min)** email: choose a mailer with double opt-in, export and delete; write the privacy note. Surfaced by: Section 3. Verify: a test subscription works and can be deleted.
- [ ] **T3 (P1, human: ~2h / CC: ~30min)** email: write the quiet-week rule and an evidence-label rule for every "what to do" line. Surfaced by: Sections 1 and 2. Verify: a sample email for the 2026-10-21 diff passes the rule.
- [ ] **T4 (P2, human: ~1h / CC: ~10min)** site: add a "not affiliated with X" line and a subscribe link. Surfaced by: Section 3. Verify: the live page shows both.
- [ ] **T5 (P2, human: ~3h / CC: ~30min)** voice.md service: write a one-page scope (what you collect, where it lives, deletion date, refund). Surfaced by: Section 2. Verify: the page exists before any sale.
- [ ] **T6 (P2, human: ~2h / CC: ~20min)** briefing: sanitize parameter names and values before they reach markdown or an email. Surfaced by: Section 3. Verify: a test with hostile names passes. Also covered by the next `/cso` step.
- [ ] **T7 (P3, follow-up)** freelance repo: anonymization checklist for samples. Surfaced by: Section 3.

### TODO proposals (pending, none written to TODOS.md)

| TODO | Why | Priority | Depends on |
|---|---|---|---|
| Hosted linter paid tier | the largest paid idea, parked behind your gates | P3 | gates in T1, a data-handling design |
| Paid briefing tier and JSON feed | monetizes the list once it exists | P3 | list size gate |
| freelance-agent-skill public repo | second repo in the same style | P3 | repo 1 traction, anonymized samples |
| Hook and swipe packs | only with honest framing of what they do and do not predict | P3 | your measurement caveats |

### Completion summary

```
  +====================================================================+
  |            MEGA PLAN REVIEW - COMPLETION SUMMARY                   |
  +====================================================================+
  | Mode selected        | SCOPE REDUCTION                             |
  | System Audit         | repo clean; ROADMAP.md untracked; 0 stars   |
  | Step 0               | principle kept; 5 deferral proposals pending|
  | Section 1  (Arch)    | 1 weak link (quiet weeks)                   |
  | Section 2  (Errors)  | 7 capabilities mapped, 4 unknown rescues    |
  | Section 3  (Security)| 6 threats, 3 High                           |
  | Section 4  (Data/UX) | 4 edge cases noted                          |
  | Section 5  (Quality) | 0 issues (no code proposed)                 |
  | Section 6  (Tests)   | 3 tests proposed for the email path         |
  | Section 7  (Perf)    | 0 issues                                    |
  | Section 8  (Observ)  | 3 signals, no trackers                      |
  | Section 9  (Deploy)  | ordered, reversible                         |
  | Section 10 (Future)  | reversibility 2/5 to 5/5 by item            |
  | Section 11 (Design)  | SKIPPED (no UI scope)                       |
  +--------------------------------------------------------------------+
  | NOT in scope         | none declared; 4 deferral proposals pending |
  | What already exists  | written                                     |
  | Dream state delta    | written                                     |
  | Error/rescue registry| 7 capabilities, 4 unknown, 2 critical gaps |
  | Failure modes        | 5 rows, 2 critical gaps                     |
  | TODO proposals       | 4 listed, none written                      |
  | Lake score           | N/A (no scored questions answered)          |
  | unverified premises  | 3                                           |
  | Outside voice        | disabled by config                          |
  +====================================================================+
```

## GSTACK REVIEW REPORT

| Review | Runs | Status | Findings |
|---|---|---|---|
| CEO review (SCOPE REDUCTION) | 1 | issues_open | 5 proposals pending, 2 critical gaps, 3 unverified premises |
| Outside voice | 0 | disabled | codex_reviews disabled in your gstack config |

VERDICT: the principle and the free-first order hold. Do not start the paid layer, the hosted linter or a
second repo until the gates you set are met. Keep the free email and the manual voice.md test as the first
steps.

**UNRESOLVED DECISIONS:**
- D2: defer or keep the paid hosted linter (recommend defer).
- D3: defer or keep the hook and swipe packs (recommend defer, or keep with honest framing).
- D4: keep the manual voice.md setup service as the first paid test (recommend keep).
- D5: defer the paid briefing tier and JSON feed behind a list-size gate (recommend defer).
- D6: defer freelance-agent-skill as a public repo (recommend defer; keep proposals private).
