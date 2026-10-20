# Multiple accounts

Each account gets its own folder so voices never bleed into each other:

```
~/.claude/x/
  accounts.md              this file: which handle is which
  first_handle/
    voice.md               copy of templates/voice.md, filled in
    log.md                 appended on "yes" by the skills
    swipe.md               written by /x-viral
  other_handle/
    voice.md
```

Every skill takes an optional handle: `/x-post @first_handle <idea>`. With one folder present it uses that
one. With several and no handle given, it asks which account before writing a word.

## Table

| handle | role | free or Premium | voice file | off-platform goal |
|---|---|---|---|---|
| {{@handle}} | {{personal / brand}} | {{free / Premium}} | `~/.claude/x/{{handle}}/voice.md` | {{newsletter / clients / product}} |

## Rules for running more than one

- Do not post duplicative or substantially similar posts across accounts you operate. X's automation
  rules treat that as spam.
- Write each account's posts from scratch in its own voice. Never copy a draft between them.
- Keep one human in the loop for each account. Nothing in this repo logs in, posts or switches accounts.
