# Research State: Neural Skill Extraction from Multi-Agent Deliberations

## Current Stage
METHODOLOGY (Stage 4) — completed.

## Research Question
How to design a neural architecture (TCN + Cross-Attention + Constrained Decoder) that extracts structured skill definitions from Plaza multi-agent deliberation transcripts?

## Key Decisions
- ARCHITECTURE: TCN as core temporal encoder (Bai 2018) — Plaza discussions are time series
- ENCODER: Longformer for token-level encoding, frozen during initial training
- ATTENTION: 5 learnable skill query probes → cross-attention over TCN output
- DECODER: CodeLLaMA-7B + QLoRA + constrained JSON generation
- TRAINING: GPT-4 silver data bootstrap → human verify → QLoRA fine-tune
- SCOPE: Discussion → extraction only. Evolution deferred to companion paper.

## Experiment Log
| Attempt | Method | Result | Status |
|---------|--------|--------|--------|
| - | - | - | pending implementation |

## Artifacts
- literature-review.md: exists (22 verified citations)
- reasoning.md: exists (TCN selection analysis)
- methodology.md: exists (detailed pseudocode)
