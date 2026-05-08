#!/usr/bin/env python3
"""
HD Pro CLI — Production Human Design calculator.

Usage:
    python hd_pro/cli.py "1990-06-15T14:30:00+00:00"
    python hd_pro/cli.py "1990-06-15T14:30:00+00:00" --json --compact
    python hd_pro/cli.py --batch ./births.json
    python hd_pro/cli.py --benchmark
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from hd_pro.engine import HDEngine


def parse_datetime(s: str) -> datetime:
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def main():
    parser = argparse.ArgumentParser(description="HD Pro — Production Human Design Calculator")
    parser.add_argument("birth_time", nargs="?", help="ISO datetime (e.g. 1990-06-15T14:30:00+00:00)")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    parser.add_argument("--compact", "-c", action="store_true", help="Compact JSON output")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all activations")
    parser.add_argument("--batch", "-b", help="JSON file with birth dates for batch processing")
    parser.add_argument("--output", "-o", help="Output JSON file (with --batch)")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark suite")
    args = parser.parse_args()

    if args.benchmark:
        return run_benchmark()
    if args.batch:
        return run_batch(args)
    if args.birth_time:
        return run_single(args)
    
    parser.print_help()
    return 0


def run_single(args) -> int:
    try:
        dt = parse_datetime(args.birth_time)
        engine = HDEngine(dt)
        d = engine.to_dict()

        if args.json:
            if args.compact:
                out = {
                    "type": d["type"], "authority": d["authority"],
                    "profile": d["profile"], "cross": d["cross_full"],
                    "definition": d["definition"], "strategy": d["strategy"],
                    "centers": d["defined_centers"],
                    "channels": [f"{ch['gates'][0]}-{ch['gates'][1]}" for ch in d["defined_channels"]],
                    "gates": d["activated_gates"],
                }
            else:
                out = d
            print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
        else:
            print(engine.summary_text())
            if args.verbose:
                print()
                print("=== ACTIVATIONS ===")
                for a in d["activations"]:
                    print(f"  {a['imprint']:12} {a['planet_symbol']} {a['planet']:12} "
                          f"G{a['gate']:2d}.{a['line']}.{a['color']}.{a['tone']}.{a['base']}  "
                          f"lon={a['longitude']:.4f}°")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        return 1


def run_batch(args) -> int:
    batch_file = Path(args.batch)
    if not batch_file.exists():
        print(f"File not found: {batch_file}", file=sys.stderr)
        return 1

    data = json.loads(batch_file.read_text())
    births = data if isinstance(data, list) else data.get("births", [])

    results = []
    for i, entry in enumerate(births):
        dt_str = entry if isinstance(entry, str) else entry.get("datetime", entry.get("birth", ""))
        label = entry.get("label", f"#{i+1}") if isinstance(entry, dict) else f"#{i+1}"
        try:
            dt = parse_datetime(dt_str)
            engine = HDEngine(dt)
            d = engine.to_dict()
            d["_label"] = label
            results.append(d)
            cross_short = d["cross_full"].split("(")[0].strip()
            print(f"[{i+1}/{len(births)}] {label}: {d['type']} {d['profile']} {cross_short}")
        except Exception as e:
            print(f"[{i+1}/{len(births)}] {label}: ERROR — {e}", file=sys.stderr)

    if args.output:
        Path(args.output).write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str))
        print(f"\nSaved {len(results)} results to {args.output}")

    return 0


def run_benchmark() -> int:
    tests = [
        {"label": "Ra Uru Hu",      "dt": "1948-04-09T05:05:00+00:00"},
        {"label": "Y2K Noon",       "dt": "2000-01-01T12:00:00+00:00"},
        {"label": "Spring 1990",    "dt": "1990-03-15T08:00:00+00:00"},
        {"label": "Summer '85",     "dt": "1985-07-20T06:30:00+00:00"},
        {"label": "Fall '75",       "dt": "1975-10-10T14:00:00+00:00"},
        {"label": "Winter '60",     "dt": "1960-12-25T03:00:00+00:00"},
        {"label": "Modern A",       "dt": "1995-05-15T18:00:00+00:00"},
        {"label": "Modern B",       "dt": "2005-08-08T08:08:00+00:00"},
        {"label": "Modern C",       "dt": "2010-11-11T11:11:00+00:00"},
        {"label": "Modern D",       "dt": "2020-12-31T23:59:00+00:00"},
        {"label": "DST Edge",       "dt": "2023-03-12T06:30:00+00:00"},
        {"label": "Leap Year",      "dt": "2024-02-29T12:00:00+00:00"},
        {"label": "Near J2000",     "dt": "2000-01-01T00:00:00+00:00"},
        {"label": "Pre-2000",       "dt": "1901-06-15T12:00:00+00:00"},
        {"label": "Mid 20th",       "dt": "1955-12-12T18:30:00+00:00"},
        {"label": "Cusp Spring",    "dt": "1988-03-20T23:59:00+00:00"},
        {"label": "Cusp Fall",      "dt": "1988-09-23T00:01:00+00:00"},
        {"label": "Midnight Edge",  "dt": "1999-12-31T23:59:59+00:00"},
        {"label": "Year 1900",      "dt": "1900-01-01T12:00:00+00:00"},
        {"label": "Year 2050",      "dt": "2050-06-15T12:00:00+00:00"},
        {"label": "DST Forward",    "dt": "2024-03-10T07:00:00+00:00"},
        {"label": "DST Back",       "dt": "2024-11-03T06:00:00+00:00"},
        {"label": "Reagan",         "dt": "1911-02-06T08:00:00+00:00"},
        {"label": "Einstein",       "dt": "1879-03-14T11:30:00+00:00"},
        {"label": "Marie Curie",    "dt": "1867-11-07T12:00:00+00:00"},
    ]

    print(f"{'#':3} {'Label':16} {'Type':24} {'Auth':18} {'Profile':8} {'C':2} {'Ch':2} {'Cross'}")
    print("-" * 120)
    ok = 0
    for i, b in enumerate(tests):
        try:
            dt = parse_datetime(b["dt"])
            engine = HDEngine(dt)
            d = engine.to_dict()
            cross_short = d["cross_full"].split("(")[0].strip()[:42]
            print(f"{i:3d} {b['label']:16} {d['type']:24} {d['authority']:18} "
                  f"{d['profile']:8} {d['center_count']:2d} {d['channel_count']:2d} {cross_short}")
            ok += 1
        except Exception as e:
            err = str(e)[:55]
            print(f"{i:3d} {b['label']:16} ERROR: {err}")

    print("-" * 120)
    print(f"\n{ok}/{len(tests)} benchmarks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
