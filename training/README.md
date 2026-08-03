# Training

Milestone 1 ships with the pretrained, Apache-2.0-licensed **Kokoro-82M**
weights and does not train a model from scratch (see `docs/ROADMAP.md` for
why: real proprietary voice training needs hundreds of GPU-hours of studio
quality audio, which is a separate, data-acquisition-led workstream).

Planned uses of this directory in later milestones:

- **Voice fine-tuning**: adapt Kokoro's StyleTTS2 decoder on a licensed
  Eixora-brand voice dataset for a truly proprietary default voice.
- **Emotion-conditioned model**: fine-tune or distill an
  emotion-embedding-capable architecture (e.g. StyleTTS2 full, or a
  CosyVoice2-style model) to replace the heuristic emotion layer in
  `text/emotion.py`.
- **Voice cloning**: few-shot speaker adaptation for custom brand voices.

None of this blocks production use of Milestone 1.
