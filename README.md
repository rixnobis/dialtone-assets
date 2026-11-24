# dialtone-assets

Recorded voices for [dialtone](https://github.com/rixnobis/dialtone)'s phone books mode: the people
who pick up, and the supervisor. A first set to hear how quickly it wears: 44 lines, 12 callers and
one supervisor. The game works without any of this; see dialtone's README for how to pack it in.

- `lines.json`: every line, who says it and when (`greet` when they pick up and listen, `hangup`
  when they hang up on you, `sale` / `nosale` at the end of a call they listened to, `sup_*` when
  you answer the corp).
- `voices.json`: each caller as a description and a reference sentence.
- `vag/`: the lines as VAG files, 8000 Hz mono, telephone band, what the game loads.
- `tools/render.py`: renders every line with Qwen3-TTS (Apache-2.0). VoiceDesign invents a voice
  from the description once, and the Base model clones that reference for every line, three takes
  each with different seeds.
- `tools/pick.py`: keeps the take whose transcript matches the line, given a transcript of every
  take (any speech-to-text that writes `{path: {"text", "dur"}}`).
- `tools/make_vags.py`: trims, band-limits, resamples and encodes the picked takes
  (`tools/spu_adpcm.py` is the SPU ADPCM encoder).

To change a line, edit `lines.json`, render, pick, `make_vags.py`, and re-pack in dialtone.
