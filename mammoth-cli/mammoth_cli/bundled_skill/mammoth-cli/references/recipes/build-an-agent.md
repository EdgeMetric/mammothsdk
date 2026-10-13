# Building an agent

The charter is the method: the job, the ordered steps, what counts as a
finding, the report format and what the agent never does. Write it first.

```bash
mammoth agent create KEY --input '{"name": "Margin watch", "charter": "...", "role": "read", "project_ids": [12]}'
mammoth agent goldens add KEY --input '{"question": "...", "expected": "..."}'
mammoth agent goldens run KEY
mammoth agent goldens status KEY
mammoth agent publish KEY
```

- The role is `read` or `write`. A new agent proposes changes for
  approval; keep that unless the owner asks otherwise
  (`agent access set KEY --input '{"role": "write", "propose": false}'`).
- Add a golden for each question a right agent must answer, then run the
  proof and read `agent goldens status` until it is finished. Failed goldens
  are shown, not blocking: fix the charter (`agent charter set KEY --input
  '{"charter": "..."}'`; `agent charter versions` and `agent charter restore`
  go back) and run again. `agent publish` is refused without a finished run
  for the current charter.
- `agent projects set KEY --input '{"project_ids": [12, 15]}'` chooses where
  it works; `agent projects clear KEY` empties that list.
- `agent feedback list KEY` shows the thumbs up and down people gave it.

An agent running inside the app saves learned facts with `agent memory add
KEY --project P --input '{"name": "...", "content": "..."}'` and working notes
with `agent scratch set KEY NAME --project P --input '{"content": "..."}'`.
