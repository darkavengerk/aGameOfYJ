# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**영조의나라 (A Game of Yeongjo)** — A Joseon Dynasty political board game set during King Yeongjo's era (2–4 players, 60–90 min). The repo's primary purpose is to generate game component images and package them into a Tabletop Simulator (TTS) save file.

## Commands

```bash
# Install dependency
pip install Pillow

# Full build: generates all images, card sheets, TTS JSON, and preview HTML
python build.py
```

There are no tests or linters. CI runs `python build.py` automatically on every push to `master` and commits the output back to the repo via `git add -f`.

## Architecture

### Data → Image → TTS Pipeline

The build runs 5 sequential steps in `build.py`:

1. **Generate individual PNGs** — reads `data/cards/*.json`, `data/tokens/*.json`, `data/board/*.json` → writes to `prototype/images/` (gitignored)
2. **Create TTS card sheets** — packs PNGs into 10×7 JPEG grids (≤2MB each, quality 85%→50%); last slot is always the hidden "영조의나라" card
3. **Convert boards to JPEG**
4. **Build TTS save file** — writes `deploy/yeongjo_kingdom.json` with `ObjectStates[]` (decks, boards, tokens), GitHub raw CDN URLs, and 6-char hex GUIDs
5. **Generate preview HTML** — writes `deploy/index.html`

All `deploy/` outputs are gitignored but force-committed by CI.

### Key Source Files

| File | Role |
|------|------|
| `build.py` | Entire build orchestrator (~776 lines) |
| `prototype/scripts/config.py` | Card dimensions (300×420px), board size (2400×1800px), colors, Korean font auto-detection |
| `prototype/scripts/data_generator.py` | Generic JSON→PNG renderer for policy/event/token/board types |
| `prototype/scripts/gapja_generator.py` | Specialized renderer for 60갑자 cards (천간×지지 combinations) |
| `prototype/scripts/card_layout_engine.py` | Abstract `CardLayout` base class + `GapjaCardLayout` implementation |
| `docs/생성규칙.md` | TTS spec: image rules, card sheet constraints, JSON structure rules |

### Data Schema

Game content lives in `data/cards/` as JSON. Key files:
- `policy_cards.json`, `event_cards.json` — standard cards with `id`, `title`, `content`, `cost`, `effect`
- `noron_gapja.json`, `soron_gapja.json` — 60 cards each (노론/소론 factions), one per 천간+지지 combination
- `ganzi_colors.json`, `five_elements.json`, `zodiac_animals.json` — lookup data used during rendering
- `gapja_cards.json` — layout config (element positions, font sizes) for 갑자 card rendering

### TTS JSON Structure

Each card gets `CardID = deck_index * 100 + card_offset`. Deck metadata references card sheet URLs on `raw.githubusercontent.com/darkavengerk/aGameOfYJ/master/deploy/images/`. The `NumWidth`/`NumHeight` in `CustomDeck` must match the actual grid dimensions of the sheet image.

### Korean Font Detection

`config.py` auto-detects fonts in order: `malgun.ttf` (Windows) → WenQuanYi (Linux CI) → AppleGothic (macOS). The CI workflow installs `fonts-wqy-zenhei` for Linux rendering.

## Deployment

Push to `master` → GitHub Actions builds and commits `deploy/` + `index.html` back to `master`. One-time setup required: GitHub repo Settings → Actions → General → Workflow permissions → Read and write.
