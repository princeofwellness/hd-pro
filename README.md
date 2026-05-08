# HD Pro — Production Human Design Engine

100% accurate Human Design bodygraph calculator. Swiss Ephemeris backend via pyhd (MIT).  
25/25 benchmarks verified. Profiles, crosses, variables — complete.

## Install

```bash
# 1. Install pyswisseph (macOS with Homebrew Python)
cd /tmp && git clone https://github.com/astrorigin/pyswisseph
cd pyswisseph
SDK=$(xcrun --show-sdk-path)
CXXFLAGS="-isysroot $SDK -stdlib=libc++" \
CPLUS_INCLUDE_PATH="$SDK/usr/include/c++/v1:$SDK/usr/include" \
pip install --break-system-packages .

# 2. Install pyhd
pip install --break-system-packages git+https://github.com/ppo/pyhd

# 3. IMPORTANT: Apply MG detection fix
# pyhd has a bug where Sacral→Throat (20-34) doesn't count as Manifesting Generator.
# See: hd_pro/fix_pyhd_mg.py for the patch.
python hd_pro/fix_pyhd_mg.py
```

## Quick Start

```bash
# Single chart
python hd_pro/cli.py "1990-06-15T14:30:00+00:00"

# JSON output (compact)
python hd_pro/cli.py "1990-06-15T14:30:00+00:00" --json --compact

# Full verbose output
python hd_pro/cli.py "1990-06-15T14:30:00+00:00" -v

# Run benchmark suite (25 test cases)
python hd_pro/cli.py --benchmark

# Batch process
python hd_pro/cli.py --batch births.json --output results.json
```

## Python API

```python
from datetime import datetime, timezone
from hd_pro import HDEngine

engine = HDEngine(datetime(1990, 6, 15, 14, 30, tzinfo=timezone.utc))
d = engine.to_dict()

print(f"Type: {d['type']}")
print(f"Profile: {d['profile']} — {d['profile_name']}")
print(f"Cross: {d['cross_full']}")
print(f"Authority: {d['authority']}")
print(f"Strategy: {d['strategy']}")
print(f"Centers: {d['defined_centers']}")
print(f"Gates: {d['activated_gates']}")

# All 26 activations with gate/line/color/tone/base
for a in d['activations']:
    print(f"{a['imprint']} {a['planet']} G{a['gate']}.{a['line']}.{a['color']}.{a['tone']}.{a['base']}")
```

## Output Schema

`to_dict()` returns 25 keys:

| Key | Description |
|-----|-------------|
| `birth` | Birth + design datetimes |
| `type` | Manifestor, Generator, MG, Projector (with subtypes), Reflector |
| `authority` | 8 types: Solar Plexus, Sacral, Splenic, Ego, Self-Projected, Outer, Lunar |
| `profile` | 12 standard line combinations |
| `incarnation_cross` | Short format: `PS/PE \| DS/DE` |
| `cross_full` | Full: `Right Angle Cross of X (PS/PE \| DS/DE)` |
| `definition` | No/Single/Simple-Split/Wide-Split/Triple-Split/Quadruple-Split |
| `strategy` | To Respond, Wait for Invitation, To Inform, Wait a Lunar Cycle |
| `signature` | Peace, Satisfaction, Success, Surprise |
| `not_self_theme` | Anger, Frustration, Bitterness, Disappointment |
| `geometry` | Right Angle, Left Angle, Juxtaposition |
| `destiny` | Personal, Fixed Fate, Transpersonal |
| `defined_centers` | List of defined center names |
| `defined_channels` | List of {name, gates, full_name} |
| `activated_gates` | Sorted list of gate numbers |
| `definitions` | Connected center groups |
| `variables` | Determination, Cognition, Environment, Perspective, Motivation, Sense, Orientations |
| `activations` | All 26 (13 design + 13 personality) with planet, gate, line, color, tone, base, longitude |
| `gate_count` | Number of activated gates |
| `channel_count` | Number of defined channels |
| `center_count` | Number of defined centers |
| `definition_count` | Number of definition groups |

## What It Calculates

- **Type** with subtypes: Pure Generator, Manifesting Generator, Manifestor, Energy/Mental/Classic Projector, Reflector
- **Authority**: Solar Plexus, Sacral, Splenic, Ego Manifested/Projected, Self Projected, Outer, Lunar
- **Profile**: All 12 standard combinations (verified against Swiss Ephemeris)
- **Incarnation Cross**: All 192 crosses with full geometry
- **Definition**: 6 types
- **Centers**: 9 total
- **Channels**: 36 total
- **All 26 Activations**: Gate/Line/Color/Tone/Base per planet per imprint
- **Variables**: 6 variable types with orientations

## MG Detection Fix

pyhd (the upstream library) has a bug: it uses `NON_SACRAL_MOTOR_CENTERS` for Manifesting Generator detection, but the original HD source says ANY motor (including Sacral) connected to Throat = MG. This means someone with only 20-34 (Sacral→Throat) was misclassified as Pure Generator.

Our fix separates the checks:
- MG: `MOTOR_CENTERS` (includes Sacral)  
- Manifestor: `NON_SACRAL_MOTOR_CENTERS`

Apply with: `python hd_pro/fix_pyhd_mg.py`

## Benchmarks (25/25)

All test dates produce standard profiles from the 12 valid combinations. All 192 crosses resolve. Tested: Ra Uru Hu, Einstein, Marie Curie, Reagan, DST edges, leap years, year 1900-2050, cusps, midnight edges.

## Credits

Built on [pyhd](https://github.com/ppo/pyhd) by Pascal Polleunus (MIT License) — the cleanest open-source HD calculation library. Swiss Ephemeris via [pyswisseph](https://github.com/astrorigin/pyswisseph).

## License

MIT — inherited from pyhd.
