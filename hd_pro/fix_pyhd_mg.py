#!/usr/bin/env python3
"""
Fix pyhd Manifesting Generator detection bug.

pyhd uses NON_SACRAL_MOTOR_CENTERS for MG detection.
But the HD source says ANY motor (including Sacral) → Throat = MG.
This means 20-34 (Sacral→Throat) was misclassified as Pure Generator.

This script patches the installed pyhd chart.py.
Run after installing pyhd.
"""

import pyhd.chart as chart_module
import inspect

SOURCE = inspect.getsource(chart_module)

# Find the buggy section
OLD = '''        has_throat_connection = self.is_connected(Centers.THROAT, NON_SACRAL_MOTOR_CENTERS)

        # Generators.
        if self.has_center(Centers.SACRAL):
            if has_throat_connection:
                return Types.MANIFESTING_GENERATOR

            return Types.PURE_GENERATOR

        # Manifestors.
        if has_throat_connection:
            return Types.MANIFESTOR'''

NEW = '''        has_non_sacral_motor_to_throat = self.is_connected(Centers.THROAT, NON_SACRAL_MOTOR_CENTERS)
        has_any_motor_to_throat = self.is_connected(Centers.THROAT, MOTOR_CENTERS)

        # Generators.
        if self.has_center(Centers.SACRAL):
            if has_any_motor_to_throat:
                return Types.MANIFESTING_GENERATOR

            return Types.PURE_GENERATOR

        # Manifestors.
        if has_non_sacral_motor_to_throat:
            return Types.MANIFESTOR'''

if OLD in SOURCE:
    print("Bug found — applying fix...")
    chart_path = chart_module.__file__
    with open(chart_path) as f:
        content = f.read()
    content = content.replace(OLD, NEW)
    with open(chart_path, 'w') as f:
        f.write(content)
    print(f"✅ Fixed {chart_path}")
    print("MG detection now uses MOTOR_CENTERS (including Sacral).")
    print("Manifestor detection still uses NON_SACRAL_MOTOR_CENTERS.")
elif NEW in SOURCE:
    print("✅ Already fixed.")
else:
    print("⚠️  Source doesn't match expected pattern — may already be patched or different version.")
    print("Checking if fix is needed...")
    # Test a known case: 20-34 only = should be MG
    from datetime import datetime, timezone
    from pyhd import Chart
    dt = datetime(1997, 2, 19, 10, 9, tzinfo=timezone.utc)
    chart = Chart(dt)
    chart_type = str(chart.type)
    if chart_type == "Pure Generator":
        print(f"❌ Bug still present — got '{chart_type}' for 20-34 only case. Manual fix needed.")
    elif "Generator" in chart_type and "Manifesting" in chart_type:
        print(f"✅ Already working — got '{chart_type}'.")
    else:
        print(f"Got '{chart_type}' — unknown if correct.")
