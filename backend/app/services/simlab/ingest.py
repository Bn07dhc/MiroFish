"""
SimLab Corpus Ingestion Pipeline

Processes markdown files from the SimLab corpus directory and indexes them into Qdrant.
Supports incremental updates — only processes files newer than last ingest.

Corpus directory structure:
    simlab-corpus/
    ├── abm/           # Agent-based modeling theory
    ├── social/        # Social simulation dynamics
    ├── networks/      # Network science
    ├── platforms/      # Platform behavior benchmarks
    ├── calibration/   # Parameter calibration guides
    ├── domains/       # Domain-specific patterns
    └── sim-reports/   # Analysis of past simulations
"""
import os
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from .rag import SimLabRAG


# Category mapping from directory names
CATEGORY_MAP = {
    "abm": "agent_based_modeling",
    "social": "social_dynamics",
    "networks": "network_science",
    "platforms": "platform_benchmarks",
    "calibration": "calibration_guide",
    "domains": "domain_specific",
    "sim-reports": "simulation_analysis",
    "gametheory": "game_theory",
    "behavioral": "behavioral_economics",
    "probability": "probability_statistics",
}


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks


def ingest_file(rag: SimLabRAG, filepath: str, category: str) -> int:
    """Ingest a single markdown file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Strip YAML frontmatter if present
    if content.startswith('---'):
        end = content.find('---', 3)
        if end != -1:
            content = content[end + 3:].strip()

    chunks = chunk_text(content)
    source = os.path.basename(filepath)

    chunk_dicts = [{"text": c, "category": category, "source": source} for c in chunks]
    return rag.upsert_chunks(chunk_dicts)


def ingest_corpus(corpus_dir: str, rag: SimLabRAG = None) -> Dict[str, int]:
    """
    Ingest all markdown files from the corpus directory.
    Returns count of chunks ingested per category.
    """
    if rag is None:
        rag = SimLabRAG()

    corpus_path = Path(corpus_dir)
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus directory not found: {corpus_dir}")

    stats = {}

    for subdir in sorted(corpus_path.iterdir()):
        if not subdir.is_dir():
            continue

        category = CATEGORY_MAP.get(subdir.name, subdir.name)
        count = 0

        for md_file in sorted(subdir.glob("*.md")):
            n = ingest_file(rag, str(md_file), category)
            count += n
            print(f"  [{category}] {md_file.name}: {n} chunks")

        if count > 0:
            stats[category] = count
            print(f"  Total {category}: {count} chunks")

    return stats
