---
name: x-dm
description: >-
  Draft founder and freelancer outreach DMs for X: one first message and two
  follow-ups, then stop. Use when the user says "write a DM to", "cold outreach",
  "how do I follow up", "message this founder", or is reaching out to a specific
  person. One-to-one, hand-sent, never bulk. Never sends.
---

# x-dm

For a freelancer or founder reaching out to a specific person they have a real
reason to contact. Three messages at most per person. Then stop.

No tool of its own. Run each message through `/x-human`, and count with
`../x-post/xcount.py` if the user wants it short.

## How this stays within X's automation rules (not a guarantee)

X's automation rules forbid unsolicited DMs in bulk or automated form, and ask
people to be thoughtful about contact frequency. So:

- **One person at a time, written for that person, sent by hand.**
- **No templates with merge fields.** If the message would work with another name
  swapped in, it is not ready.
- **Never a list.** Do not generate messages for a batch of accounts. If the user
  pastes twenty profiles, pick the one or two with a real reason and say why the
  rest are not worth a DM.
- Note that someone being able to receive your DM does not mean they want it.

## Before you write

1. Read `~/.claude/x/voice.md`.
2. Ask: who is this, what did you see of theirs (a specific post, a pricing page, a
   launch), what do you offer, what is the smallest next step. If the user has no
   specific observation, there is nothing to write yet. Say so.
3. **No invented proof.** A number, client or result the user did not give becomes
   `{{your number}}`, flagged.

## The sequence

**Message 1: the first message.** Four parts, under about 450 weighted characters:
the specific thing you noticed, why it made you write, the one-line offer, a
question that costs one word to answer ("worth a quick look?"). No pitch deck, no
calendar link in the first message, no "I hope this finds you well".

**Message 2: follow-up, 4 to 7 days later.** Add one new, useful thing: a fix, a
data point, a short example. Not "just bumping this".

**Message 3: last one, 7 to 10 days later.** Shorter. Give an easy exit ("no worries
if the timing is off") and leave the door open. Then **stop**. No fourth message,
ever. No new account, no other channel to get around the silence.

Spacing is a suggestion. The user decides when to send.

## Checks before showing

- [ ] References something only this person has posted or built
- [ ] One ask, answerable in a word
- [ ] No links in message 1
- [ ] No flattery with nothing behind it
- [ ] No claim the user did not give
- [ ] Passed `/x-human`

## Output

Three fenced blocks, labelled 1, 2 and 3, each with the suggested day offset and a
line saying what would change the plan (a reply, a "no", a read receipt that
changes nothing). Remind the user to send them by hand and to stop at three.

## Approval gate

1. Show the finished text in one fenced block, ready to copy. If there is a link,
   show it in a second block titled FIRST REPLY.
2. End the message with: Reply yes to log it.
3. On "yes", append one line to `~/.claude/x/log.md` (or the handle's folder):
   date, skill, first line. That is all "yes" does.
4. Never post, like, follow, reply, DM or scroll. You write; the human posts, by
   hand, on x.com.
