# X rules this repo depends on

Last checked: 2026-10-21. Every rule here is paraphrased from the source linked
in its heading, with short quoted fragments. Re-read the source before you rely
on it; X edits these pages. Numbers that can go stale are also in
[stale.md](stale.md).

## Automation (why this repo never posts)

Source: https://help.x.com/en/rules-and-policies/x-automation (page marked "Updated April 2026")

- Under "Don't", X lists "non-API-based forms of automation, such as scripting the X website" and says
  these "may result in the permanent suspension" of the account.
- The user is "ultimately responsible" for actions taken with their account or by apps associated with it.
- Automated replies and mentions: replying to posts based on keyword searches alone is not allowed.
  Automated replies need an opt-in from the recipient.
- Automated DMs: unsolicited DMs in bulk or automated form are not allowed.
- Automated likes and hiding replies are not allowed.
- AI-powered automated reply bots need prior written approval from X.
- Human approval of each post does not change any of this. The rule is about who performs the action.

What follows for this repo: the skills write text. A person reads it and posts it by hand, one action at a
time. Nothing here posts, likes, follows, replies, DMs, scrolls or scrapes, and `/x-dm` drafts one-to-one
messages for a person to send themselves.

## Original Content Rewards

Source: https://help.x.com/en/using-x/original-content-rewards

Replaced Creator Revenue Sharing. Revenue Sharing stopped taking new enrollments on 2026-08-07 and ended on
2026-09-07. From 2026-09-08 existing members could apply for the new program.

Eligibility (all required at application):

| requirement | value |
|---|---|
| plan | active Premium, Premium+ or Premium Business (or the equivalent The X Subscription plan) |
| verified followers | at least 500 |
| Home Timeline impressions from verified users, last 90 days, replies excluded | at least 500,000 |
| age | 18+ |
| country | one of the listed countries (the page lists them; check yours) |
| account | personal or business, in good standing, no political or government organisations |
| content | actively post original content |

- Meeting the criteria does not guarantee admission. Apply in Creator Studio; X reviews. One appeal, then reapply after 42 days.
- Payouts: processed every two weeks, $30 minimum. US users are paid through X Money, others through Stripe.
- X publishes no per-impression rate.
- Payout impressions are "qualified impressions": unique impressions from Premium users on the Home
  Timeline where at least 50% of the post is visible. This is a different pool from the
  verified-viewer impressions used for the eligibility threshold.

Ineligible content (the linter flags the patterns it can see):

- copied or substantially reproduced content, content downloaded and re-uploaded, minimally modified
  content, aggregated content, cross-platform reposts by someone other than the creator
- content "exclusively focused on monetization coaching, monetization discussion, or maximizing payouts"
- content "created or posted using automated means"
- content with a helpful Community Note, disinformation, or content that breaks other rules

Continuous eligibility includes: no automated tools to generate likes, follows, views, comments or shares,
and no soliciting engagement ("repeatedly instructing users to engage", such as asking to like, reply,
bookmark, follow or repost). The linter flags every instance, because one bait line is still a ranking and
review risk.

Also in force since 2026-03-03: AI-generated videos of an armed conflict without an AI disclosure lead to a
90-day suspension from the program.

## Subscriptions

Reported gate: 2,000 verified followers and 5M impressions; creator keeps up to about 97% on web.
**Not verified against a primary source. Check the app before you encode or quote it.**

## Limits

| item | value | status |
|---|---|---|
| post, free account | 280 weighted characters | twitter-text config v3 (public), verified |
| post, any Premium tier | 25,000 characters | X Premium help page, read via search 2026-10-21: https://help.x.com/en/using-x/x-premium |
| URL | counts 23 whatever its length | twitter-text config v3, verified |
| CJK, most emoji | weigh 2 | twitter-text config v3, verified |
| bio | 160 characters | from the brief; confirm in the app |

Weighted counting source: https://github.com/twitter/twitter-text/blob/master/config/v3.json
