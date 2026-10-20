# Numbers that go stale

Every number in the skills that can change, with where it came from and how sure we are.
Update the row and the date when you re-check. "Unverified: measure before shipping" means the skill
must not state it as fact.

| item | value in repo | checked | source | status |
|---|---|---|---|---|
| ranking weights (all) | see x-algorithm.md | 2026-10-21 | https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/param.rs at commit 74d49a4 | verified, regenerate with `weights.py` |
| reply scored 0-3 by a Grok model when parent or root has over 250,000 followers | 250,000 | 2026-10-21 | `grox/flows/reply_spam/constants.py`, `task_filter.py` at 74d49a4 | verified in code; the rubric prompt is not published |
| multi-step reply-spam filter, root followers | 1,000 | 2026-10-21 | `grox/flows/reply_spam/task_multi_step_reply_spam.py` at 74d49a4 | verified in code |
| coordinated-spam filter, root followers | 180,000 | 2026-10-21 | `task_filter.py` at 74d49a4 | verified in code |
| link posts reach less (non-Premium) | observed, not coded | 2026-10-21 | Buffer analysis of 18.8M posts, March 2025 (secondary) | observed, not coded; no link penalty in param.rs |
| reply downvotes list "AI generated" | March 2026, Premium | 2026-10-21 | brief / secondary reporting | unverified: measure before shipping |
| OCR verified followers | 500 | 2026-10-21 | https://help.x.com/en/using-x/original-content-rewards | verified |
| OCR impressions | 500,000 in 90 days, replies excluded | 2026-10-21 | same | verified |
| OCR payout cadence and minimum | every 2 weeks, $30 | 2026-10-21 | same | verified |
| OCR per-impression rate | none published | 2026-10-21 | same | verified absence |
| Revenue Sharing end date | 2026-09-07 | 2026-10-21 | same | verified |
| Subscriptions gate | 2,000 verified followers, 5M impressions | 2026-10-21 | brief | unverified: check in the app |
| Subscriptions creator share | up to ~97% on web | 2026-10-21 | brief | unverified: check in the app |
| post length, free | 280 weighted | 2026-10-21 | twitter-text config v3 | verified |
| post length, Premium | 25,000 | 2026-10-21 | https://help.x.com/en/using-x/x-premium (via search) | verified, secondary read |
| URL weight | 23 | 2026-10-21 | twitter-text config v3 | verified |
| bio length | 160 | 2026-10-21 | brief | unverified: confirm in the app |
| Automation rules page | "Updated April 2026" | 2026-10-21 | https://help.x.com/en/rules-and-policies/x-automation | verified |
| "Show more" truncation point | not encoded | 2026-10-21 | none | unverified: measure before shipping |
| images per post | not encoded | 2026-10-21 | none | unverified: measure before shipping |
| video limits on free tier | not encoded | 2026-10-21 | none | unverified: measure before shipping |
| alt-text and poll limits | not encoded | 2026-10-21 | none | unverified: measure before shipping |
| native scheduler behaviour | not encoded | 2026-10-21 | none | unverified: measure before shipping |
| logged-out visibility | not encoded | 2026-10-21 | none | unverified: measure before shipping |

Stale 2023 figures that blogs still quote and that must not appear anywhere in the repo as fact: the old
reply, author-reply-back and report weights. They are named in `weights.py` output under "Numbers to stop quoting".
