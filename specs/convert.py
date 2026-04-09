#!/usr/bin/env python3
"""
Convert a layered YAML spec to MiroFish simulation_config.json

Usage:
    python convert.py specs/templates/attention_market.yaml -o /path/to/output/
    python convert.py specs/templates/org_deal.yaml --validate-only
"""
import argparse
import sys
import json
from pathlib import Path

# Add backend/app/services to path so 'layered' is importable directly
# This avoids triggering app/__init__.py which requires Flask
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend' / 'app' / 'services'))

from layered.schema import LayeredSimSpec, validate_spec
from layered.converter import spec_to_config, save_config


def main():
    parser = argparse.ArgumentParser(description='Convert layered YAML spec to MiroFish config')
    parser.add_argument('spec', help='Path to YAML spec file')
    parser.add_argument('-o', '--output', help='Output directory (default: prints to stdout)')
    parser.add_argument('--validate-only', action='store_true', help='Only validate, do not convert')
    parser.add_argument('--sim-id', help='Override simulation ID')
    args = parser.parse_args()

    spec = LayeredSimSpec.from_yaml(args.spec)
    errors = validate_spec(spec)

    if errors:
        print(f"Validation errors:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    if args.validate_only:
        print(f"Valid: {spec.name} v{spec.version}")
        print(f"  Domain: {spec.world.domain}")
        print(f"  Language: {spec.world.language}")
        if spec.population.mode == "template":
            print(f"  Agents: {spec.population.total_agents} ({len(spec.population.archetypes)} archetypes)")
        else:
            print(f"  Agents: {len(spec.population.named_agents)} (named)")
        total_rounds = (spec.dynamics.total_simulation_hours * 60) // spec.dynamics.minutes_per_round
        print(f"  Rounds: {total_rounds}")
        print(f"  Phases: {len(spec.world.phases)}")
        sys.exit(0)

    config = spec_to_config(spec, simulation_id=args.sim_id)

    if args.output:
        path = save_config(config, args.output)
        print(f"Config saved to: {path}")
    else:
        print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
