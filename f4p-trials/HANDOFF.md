# Fuel 4 Performance trial-reel campaign (handoff)

**Goal (from the user):** repost every Fuel 4 Performance interview (Ep. 1-7) as Instagram **trial reels**,
on a schedule, with a change in each version, to reach non-followers and convert them to followers on @fueled_4_fitness.

**Agreed plan:** 3 trial reels a day at 4:22 PM Arizona time (America/Phoenix, no DST), for 14 days, from Nov 14
to Nov 27, 2026. 7 episodes × 6 variants = 42 posts. `publish_f4p.py: slots_for(date)` gives each day's (ep, variant) list.
The episode order is in `plan.json` (4, 7, 5, 6, 1, 2, 3). Every episode gets variant 1 first, then 2, and so on.

## Variants (`plan.json` → `variants`)
| v | change |
|---|---|
| 1 | cold open (starts at the actual question; the 10-20 s intro is why viewers left at ~9-16 s) |
| 2 | 1.1x speed |
| 3 | cold open + 1.1x |
| 4 | 1.05x + punchier color + hook text in the bottom blur band |
| 5 | cold open + 1.05x + burned-in captions |
| 6 | cold open + 1.1x + punchy + hook + captions |

## Sources
- Ep. 5, 6, 7: full-quality finished edits in the repo (`dji-reel/jensen_full_interview_reel.mp4`,
  `kulasingam-reel/kulasingam_interview_reel.mp4`, `squires-reel/squires_interview_reel.mp4`).
- Ep. 1-4: the user uploaded raw 4K originals to Drive ("Johnson / ROC / Dickey / Livvy interview OG.mp4").
  The posted versions had black bars or were horizontal, so they are rebuilt in the blurred vertical layout
  (`render.py base EP`) from 1440p proxy pieces on branch `dji-transfer` under `f4p/ep{N}/`.
  - Ep. 4: all pieces transferred (5 s pieces q00-q06).
  - Ep. 1: q00-q03 transferred (4 s pieces); Ep. 2 and 3: none yet. Finish with `sandbox_transfer.py`:
    paste it into the Composio workbench (session_id "part"), then call `nxt()` once per cell until the queue is empty.
    About 40 s per call; it rebuilds the queue from what is already on the branch.
- `transcripts.json`: word timestamps for all 7 episodes (whisper base.en) plus the original captions.
  For Ep. 7 the timestamps come from the IG copy, which starts about 0.42 s later than the repo file (`shift`).

## Rendering (run locally, not in the sandbox, which has 1 CPU and <1 GB RAM)
```
cd f4p-trials
python3 render.py base 1            # after its proxy pieces are all on dji-transfer
python3 render.py var 6 1 6 2 ...   # writes out/ep{E}_v{V}.mp4 (about 1.5 min each)
python3 render.py caps 6            # print the caption groups to proof-read
```
Commit and push each `out/*.mp4` to `claude/file-access-question-oa157h` **before** its post day. The publisher
fetches it from that branch.

**Done so far:** `out/ep4_v1`, `ep7_v1`, `ep5_v1` (today, Nov 14) and `ep4_v6` (test). Next due: Nov 15 needs
`ep6_v1`, `ep1_v1`, `ep2_v1`; Nov 16 needs `ep3_v1`, `ep4_v2`, `ep7_v2`.

## Publishing
`publish_f4p.py` runs in the Composio workbench. Bootstrap it from the branch (see the file header), then
`for ep, v in slots_for(AZ_DATE): publish_slot(ep, v)`. Re-call until each returns POSTED or "already posted".
It skips a caption that is already live, so it never double-posts. Trial reels use
`trial_params.graduation_strategy = MANUAL`; check `is_shared_to_feed == False`.
Then message the user the 3 permalinks and what changed in each.

## Gotchas learned
- The Composio sandbox pauses between calls and kills a cell when the MCP call times out (60 s). Keep each call under about 50 s.
- `/mnt/files` in the sandbox has been wiped between days, so keep everything durable in this repo.
- The user dislikes yellow text. Use white with a black stroke (Anton font, included here).
