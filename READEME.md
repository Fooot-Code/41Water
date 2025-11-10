# 41 Water — Pixel Adventure (Pygame)

## Overview
"41 Water" is a small pixel-art adventure built with Pygame. You play as one of several classes (Wizard, Worrier, Ranger) and traverse 3 levels to drink the mythical "41 Water". A friendly guide accompanies you — but beware: they become the final boss. Choices you make determine one of three endings.

This codebase uses procedural pixel graphics (no external images). Sprites and tiles are generated at runtime.

## Requirements
- Python 3.8+
- pygame (install via pip)

## Install
1. Clone or download this repo.
2. From repo root:

pip install -r requirements.txt


## Run
From the project root:

python -m src.main

or

cd src
python main.py


## Controls
- Arrow keys / A/D: Move left/right
- Up / W / Space: Jump
- J: Light attack (slash)
- K: Dash attack (short invulnerable dash)
- Enter: Advance dialog / start
- Esc: Pause / quit

## Project layout
All game code lives in `src/`:
- `main.py` — entry point & main loop
- `settings.py` — tune constants like screen size, tile size
- `assets.py` — procedural pixel sprite & tile generation
- `player.py` — Player class, movement, attacks
- `enemy.py` — Enemy class (basic AI)
- `boss.py` — Final boss (guide turned enemy)
- `level.py` — Level definitions and tile collision
- `ui.py` — HUD and simple dialog system
- `game_states.py` — Manage menus, levels, endings

## How mechanics map to hollow-knight style
- Melee attack uses a short-range animated hitbox
- Dash attack gives brief speed boost and enemy damage on contact
- Enemies have simple patterns (patrol, ranged) and health

## Extending
- Add new classes in `player.py`
- Add more levels in `level.py` by adding new level definitions
- Improve pixel sprites in `assets.py` (procedural generator functions are commented)

## License
This is a sample/demo project. Use and modify freely.

Enjoy — and may you find the 41 Water!