# -*- coding: utf-8 -*-
"""TSE — TCN-Skill-Extractor.

Pipeline:
  Longformer-style token encoding (hash embed / optional Longformer)
  → TCN temporal modeling (dilated conv d=1,2,4)
  → Skill Query Cross-Attention (5 field probes)
  → Constrained JSON decoder (ChatHarness + schema grammar)

See methodology.md and reasoning.md for architecture rationale.
"""

from .config import DEFAULT_CONFIG, TSEConfig
from .dataset import ExtractionExample, PlazaExtractionDataset
from .experiments import (
    ATTENTION_DIAGNOSTIC_BOUNDARY,
    KEYWORD_ATTENTION_ALGORITHM_VERSION,
    LOCAL_BENCHMARK_BOUNDARY,
    attention_distribution_metrics,
    benchmark_local_extraction,
    build_keyword_attention,
    compare_attention_baseline,
    load_experiment_samples,
    sha256_file,
)
from .heads import MultiTaskHeads
from .pipeline import (
    TSEPipeline,
    TSEResult,
    extract_skill_moments,
    extract_skills,
    get_tse_pipeline,
)
from .schema import parse_skills_payload, validate_skill_fields
from .trainer import TrainConfig, TrainHistory, train_tse
from .transcript import PlazaTranscript, Utterance, parse_transcript

__all__ = [
    "DEFAULT_CONFIG",
    "TSEConfig",
    "TSEPipeline",
    "TSEResult",
    "PlazaTranscript",
    "Utterance",
    "parse_transcript",
    "extract_skills",
    "extract_skill_moments",
    "get_tse_pipeline",
    "parse_skills_payload",
    "validate_skill_fields",
    "PlazaExtractionDataset",
    "ExtractionExample",
    "benchmark_local_extraction",
    "build_keyword_attention",
    "attention_distribution_metrics",
    "compare_attention_baseline",
    "load_experiment_samples",
    "sha256_file",
    "KEYWORD_ATTENTION_ALGORITHM_VERSION",
    "LOCAL_BENCHMARK_BOUNDARY",
    "ATTENTION_DIAGNOSTIC_BOUNDARY",
    "MultiTaskHeads",
    "TrainConfig",
    "TrainHistory",
    "train_tse",
]
