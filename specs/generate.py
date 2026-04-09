#!/usr/bin/env python3
"""
Generate a layered sim spec using RAG-assisted knowledge retrieval.

Usage:
    python generate.py --domain "attention_economy" --description "Information brokers compete for audience share" --output spec.yaml
    python generate.py --domain "corporate_governance" --description "Korean DC acquisition" --template org_deal --output dci-v12.yaml
"""
import argparse
import sys
import json
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'backend' / 'app' / 'services'))

from simlab.rag import SimLabRAG


def main():
    parser = argparse.ArgumentParser(description='RAG-assisted sim spec generation')
    parser.add_argument('--domain', required=True, help='Simulation domain')
    parser.add_argument('--description', default='', help='Simulation description')
    parser.add_argument('--archetypes', nargs='*', default=[], help='Agent archetypes to include')
    parser.add_argument('--output', help='Output YAML file path')
    parser.add_argument('--template', help='Base template to start from (e.g., attention_market, org_deal)')
    args = parser.parse_args()

    rag = SimLabRAG()

    print(f"Retrieving knowledge for domain: {args.domain}")
    knowledge = rag.retrieve_for_spec(
        domain=args.domain,
        description=args.description,
        archetypes=args.archetypes if args.archetypes else None,
    )

    print(f"\nRetrieved {sum(len(v) for v in knowledge.values())} chunks across {len(knowledge)} categories:")
    for cat, chunks in knowledge.items():
        print(f"  {cat}: {len(chunks)} chunks")
        for c in chunks[:2]:
            print(f"    - {c[:100]}...")

    # Load template if specified
    if args.template:
        template_path = Path(__file__).parent / 'templates' / f'{args.template}.yaml'
        if template_path.exists():
            print(f"\nBase template: {template_path}")
            with open(template_path) as f:
                base = yaml.safe_load(f)
            print(f"  Agents: {base.get('population', {}).get('total_agents', '?')}")
        else:
            print(f"\nTemplate not found: {template_path}", file=sys.stderr)

    print("\n--- Retrieved Knowledge (paste into LLM for spec generation) ---\n")
    for cat, chunks in knowledge.items():
        print(f"## {cat}")
        for c in chunks:
            print(c[:500])
            print()

    if args.output:
        # Save retrieved knowledge as context file
        ctx_path = args.output.replace('.yaml', '.context.json')
        with open(ctx_path, 'w') as f:
            json.dump({"domain": args.domain, "description": args.description, "knowledge": knowledge}, f, indent=2)
        print(f"\nContext saved to: {ctx_path}")
        print("Use this with an LLM to generate the full spec YAML.")


if __name__ == '__main__':
    main()
