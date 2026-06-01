#!/usr/bin/env python3
"""
Extract SESTSAL .out (oracle) data for comparison.
Reads .out and extracts closure% at target times.
"""

from pathlib import Path
from typing import Dict, List, Tuple
import re


def parse_out(filename: str) -> Tuple[List[float], List[float], List[float]]:
    """
    Parse SESTSAL .out file.
    Returns: (times_h, depths_m, closures_ppg)
    """
    times, depths, closures = [], [], []

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('%'):
                continue

            parts = line.split()
            if len(parts) >= 3:
                try:
                    t = float(parts[0])
                    d = float(parts[1])
                    c = float(parts[2])
                    times.append(t)
                    depths.append(d)
                    closures.append(c)
                except ValueError:
                    continue

    return times, depths, closures


def closure_percent(times: List[float], closures: List[float]) -> Dict[float, float]:
    """
    Calculate closure percentage from SESTSAL output.
    closure% = (closure_initial - closure_final) / closure_initial * 100
    """
    if not closures:
        return {}

    p_initial = closures[0]
    result = {}

    for t, c in zip(times, closures):
        result[t] = (p_initial - c) / p_initial * 100

    return result


def extract_oracle_data(inp_name: str, out_path: str = 'legacy/sestsal/examples') -> Dict:
    """
    Extract oracle data from .out file for a given case.
    Returns: {case_name, closure_percent_final, closure_timeline}
    """
    out_file = Path(out_path) / (inp_name.replace('.inp', '.out'))

    if not out_file.exists():
        print("Warning: " + str(out_file) + " not found")
        return None

    times, depths, closures = parse_out(str(out_file))
    closure_pcts = closure_percent(times, closures)

    if not closure_pcts:
        return None

    final_time = max(closure_pcts.keys())
    closure_final = closure_pcts[final_time]

    return {
        'case_name': inp_name.replace('.inp', ''),
        'closure_percent_final': closure_final,
        'closure_timeline': closure_pcts,
        'duration_hours': final_time,
        'notes': ''
    }


def extract_all_oracles(examples_dir: str = 'legacy/sestsal/examples') -> List[Dict]:
    """Extract oracle data from all .inp/.out pairs."""
    examples_path = Path(examples_dir)
    oracles = []

    for inp_file in sorted(examples_path.glob('*.inp')):
        inp_name = inp_file.name
        oracle = extract_oracle_data(inp_name, examples_dir)
        if oracle:
            oracles.append(oracle)
            case_name = oracle['case_name']
            closure = oracle['closure_percent_final']
            duration = oracle['duration_hours']
            print("  " + case_name + " -> closure=" + "{:.2f}".format(closure) + "% (t=" + "{:.2f}".format(duration) + "h)")

    return oracles


def generate_cpp_header(oracles: List[Dict], output_file: str = 'include/test_sestsal_oracle.hpp'):
    """Generate C++ header with oracle data."""
    header = '''#pragma once
#include <string>
#include <vector>

struct SestSalOracle {
    std::string case_name;
    double closure_percent_final;
    double tolerance_percent;
    std::string notes;
};

const std::vector<SestSalOracle> SESTSAL_ORACLES = {
'''

    for oracle in oracles:
        case_name = oracle['case_name']
        closure = oracle['closure_percent_final']
        tolerance = 5.0
        notes = 'DM halita'

        header += '    {\n'
        header += '        "' + case_name + '",\n'
        header += '        ' + "{:.4f}".format(closure) + ',\n'
        header += '        ' + "{:.1f}".format(tolerance) + ',\n'
        header += '        "' + notes + '"\n'
        header += '    },\n'

    header += '};\n'

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header)

    print("Generated: " + output_file)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        oracle = extract_oracle_data(sys.argv[1])
        if oracle:
            print(oracle)
    else:
        print("Extracting SESTSAL oracles...")
        oracles = extract_all_oracles()
        print("Total: " + str(len(oracles)) + " cases")
        generate_cpp_header(oracles)
