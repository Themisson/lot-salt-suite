#!/usr/bin/env python3
"""
Converter SESTSAL (.inp) to SaltCreep (YAML).
"""

from pathlib import Path
from typing import Dict, Any


def parse_inp(filename: str) -> Dict[str, Any]:
    """Parse SESTSAL .inp file into structured dict."""
    result = {
        'burial_m': 5237,
        'k0': 1.0,
        'pressure_ppg': 14.75,
        'temp_K': 370.88,
        'E_Pa': 20.4e9,
        'nu': 0.36,
        'total_hours': 15,
        'mesh_radial': 50,
        'time_increments': []
    }

    with open(filename, 'r') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line or not line.startswith('%'):
            continue

        keyword = line[1:].strip()

        if keyword == 'STEP':
            try:
                n_steps = int(lines[i].strip()) if i < len(lines) else 0
            except ValueError:
                n_steps = 0
            i += 1
            for _ in range(n_steps):
                if i < len(lines):
                    # Parse: 'step 1' 5237 14.75 0
                    text = lines[i].replace("'", "").split()
                    if len(text) >= 4:
                        result['pressure_ppg'] = float(text[2])
                    i += 1

        elif keyword == 'STEP.DURATION':
            try:
                n_dur = int(lines[i].strip()) if i < len(lines) else 0
            except ValueError:
                n_dur = 0
            i += 1
            for _ in range(n_dur):
                if i < len(lines):
                    # Parse: 'step 1' 15 0 0
                    text = lines[i].replace("'", "").split()
                    if len(text) >= 2:
                        try:
                            result['total_hours'] = float(text[1])
                        except:
                            pass
                    i += 1

        elif keyword == 'OVERBURDEN':
            if i < len(lines):
                parts = lines[i].split()
                if len(parts) >= 2:
                    try:
                        result['k0'] = float(parts[0])
                        n_ovb = int(parts[1])
                    except:
                        n_ovb = 0
                else:
                    n_ovb = 0
                i += 1
            else:
                n_ovb = 0

            for _ in range(n_ovb):
                if i < len(lines):
                    parts = lines[i].split()
                    if len(parts) >= 1:
                        try:
                            result['burial_m'] = float(parts[0])
                        except:
                            pass
                    i += 1

        elif keyword == 'TEMPERATURE':
            if i < len(lines):
                parts = lines[i].split()
                n_tmp = 1
                i += 1
            else:
                n_tmp = 0

            for _ in range(n_tmp):
                if i < len(lines):
                    parts = lines[i].split()
                    if len(parts) >= 2:
                        try:
                            result['temp_K'] = float(parts[1]) + 273.15
                        except:
                            pass
                    i += 1

        elif keyword == 'LITHOLOGY':
            if i < len(lines):
                try:
                    n_lith = int(lines[i].strip())
                    i += 1
                except ValueError:
                    n_lith = 0
            else:
                n_lith = 0

            for _ in range(n_lith):
                if i < len(lines):
                    # Parse: 'Halita' 20400 0.36 ...
                    text = lines[i].replace("'", "").split()
                    if len(text) >= 3:
                        try:
                            result['E_Pa'] = float(text[1]) * 1e6
                            result['nu'] = float(text[2])
                        except:
                            pass
                    i += 1

        elif keyword == 'SETTINGS.RADIAL':
            if i < len(lines):
                try:
                    n_rad = int(lines[i].strip())
                    result['mesh_radial'] = n_rad
                except ValueError:
                    pass
                i += 1
                # Skip the settings line
                if i < len(lines):
                    i += 1

        elif keyword == 'SETTINGS.DEPTH':
            try:
                n_depth = int(lines[i].strip()) if i < len(lines) else 0
            except ValueError:
                n_depth = 0
            i += 1
            if i < len(lines) and n_depth > 0:
                parts = lines[i].split()
                if parts:
                    try:
                        result['burial_m'] = float(parts[0])
                    except:
                        pass
                i += 1

        elif keyword == 'TIME.INCREMENT':
            try:
                n_inc = int(lines[i].strip()) if i < len(lines) else 0
            except ValueError:
                n_inc = 0
            i += 1
            steps = []
            for _ in range(n_inc):
                if i < len(lines):
                    parts = lines[i].split()
                    if len(parts) >= 2:
                        try:
                            until_h = float(parts[0])
                            dt_h = float(parts[1])
                            steps.append({'until_s': until_h * 3600, 'dt_s': dt_h * 3600})
                        except:
                            pass
                    i += 1
            result['time_increments'] = steps

    return result


def dict_to_yaml(d: Dict[str, Any], case_name: str) -> str:
    """Generate YAML string from parsed dict."""
    lines = [
        f"name: {case_name}",
        "",
        "geometry:",
        "  well_radius_m: 0.155575",
        "  outer_radius_factor: 320",
        "",
        "mesh:",
        f"  n_radial: {d.get('mesh_radial', 50)}",
        "  ratio: 1.05",
        "",
        "depths:",
        f"  burial_m: {int(d.get('burial_m', 5237))}",
        "  water_depth_m: 0",
        "  salt_above_m: 0",
        "",
        "lithology: halita",
        "",
        "fluid:",
        f"  weight_lb_per_gal: {d.get('pressure_ppg', 14.75)}",
        "",
        "stress:",
        f"  k0: {d.get('k0', 1.0)}",
        "",
        "material:",
        f"  E_Pa: {d.get('E_Pa', 20.4e9):.1e}",
        f"  nu: {d.get('nu', 0.36)}",
        "",
        "thermal:",
        "  enabled: false",
        "  mode: constant",
        f"  T_K: {d.get('temp_K', 370.88)}",
        "",
        "time:",
        f"  total_s: {int(d.get('total_hours', 15) * 3600)}",
        "  dt_s: 180",
        "  scheme: explicit",
        "",
        "creep:",
        "  elastic_only: false",
        "  secondary: true",
        "  primary: false",
        "  tertiary: false",
        "  damage: false",
        "",
        "output:",
        "  every_n_steps: 10",
        "  vtu: false",
    ]

    # Add time increments if available
    increments = d.get('time_increments', [])
    if increments:
        lines.append("  steps:")
        for inc in increments:
            lines.append(f"    - until_s: {int(inc['until_s'])}")
            lines.append(f"      dt_s: {inc['dt_s']}")

    return '\n'.join(lines)


def convert_inp_to_yaml(inp_path: str, output_dir: str = 'cases/sestsal'):
    """Convert a single .inp file to YAML."""
    params = parse_inp(inp_path)
    case_name = Path(inp_path).stem
    yaml_content = dict_to_yaml(params, case_name)

    output_path = Path(output_dir) / (case_name + '.yaml')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(yaml_content)

    print("Converted: " + str(inp_path) + " -> " + str(output_path))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        convert_inp_to_yaml(sys.argv[1])
    else:
        examples_dir = Path('legacy/sestsal/examples')
        for inp_file in sorted(examples_dir.glob('*.inp')):
            convert_inp_to_yaml(str(inp_file))
