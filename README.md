# dialtone-assets

Recorded voices for a telemarketing game on the PlayStation: the people who pick up when you cold-call
them, the supervisor who checks your numbers, and the insider who leaves you sticky notes.
[dialtone](https://github.com/rixnobis/dialtone) is the proof of concept that plays them; the game works
without any of this.

The bank holds 2598 lines in 51 voices, up to three takes each, as 8000 Hz SPU ADPCM VAGs in `vag/`.
The callers' lines were written by several contributors, one writer per caller.

- `manifest.json` is the index a game should read. `voices[]` has each speaker (id, name, `tier`:
  residential, small_business or corporate, and the description its voice was designed from).
  `lines[]` has each line (`id`, `voice`, `tier`, `kind`, `text`, a delivery `tag`, and `takes`, the VAG
  paths). `set` 1 is the first 44 lines, kept under their old ids; `set` 2 is this bank. Ids are stable:
  a later pass only appends, and bumps `version`.
- Kinds: `greet` (they pick up), `hangup` (they hang up on you), `nosale` / `sale` (they listened),
  `odd` (an answering machine, a wrong guess about who you are, something at home), `callback` (they
  remember you), `sup_*` (the supervisor) and `note_*` (the insider's call).
- `voices/`: each voice's reference clip, and the delivery references (`_up`, `_hot`, `_low`, `_hush`)
  used for lines tagged that way.
- `voices.json` and `lines.json` are the render inputs; `tools/bank/` renders them with Qwen3-TTS
  (Apache-2.0): `design.py` designs candidate voices, `pick_design.py` keeps the one nearest its target
  pitch, `moods.py` and `mood_pick.py` make the delivery references, `render.py` renders the takes,
  `asr.py` transcribes them, `pick_takes.py` keeps the takes that say the line, and `make_bank.py` trims,
  band-limits and encodes them.
