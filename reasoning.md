# Research Deliberation: Neural Extraction Method Selection for Plaza Skill Discovery

## Knowledge Consolidation

From `literature-review.md`, the landscape of neural extraction methods (2020-2026) falls into three paradigms:

1. **Encoder-only architectures** (Longformer, GREAT, TCN) — produce representations but cannot generate structured output
2. **Decoder-only architectures** (GoLLIE, KnowCoder via Code-LLM) — generate structured output but lack dialogue structure awareness
3. **Pretraining strategies** (D2K contrastive) — improve representation quality but don't define a complete pipeline

No single existing method handles the full Plaza extraction pipeline: multi-turn, multi-speaker dialogue → structured skill JSON with five fields (name, description, category, instructions, required_tools).

## Criteria for Plaza-Specific Selection

| Criterion | Weight | Why it matters for Plaza |
|-----------|--------|--------------------------|
| Temporal sequence modeling | ★★★★★ | Plaza discussion is naturally a time series of utterances — the order and gaps between mentions matter |
| Structured output generation | ★★★★★ | Skills must conform to a strict JSON schema with five fields |
| Cross-turn relation capture | ★★★★ | A skill is often mentioned across multiple non-consecutive rounds |
| Long-sequence handling | ★★★ | Plaza transcripts are 2000-4000 tokens |
| Existing competency reuse | ★★★ | Our team has TCN-attention prior models and training experience |
| Low training data requirement | ★★ | No public dataset of (discussion, skill) pairs exists |

## Candidate Method Analysis

### 1. D2K contrastive learning (Yu 2022, AAAI)
- Role in pipeline: Pretraining stage only
- Outputs: Knowledge triples (s, r, o) — not structured skill JSON
- Verdict: EXCLUDED — cannot generate instructions text; no generation capability at all. Useful for pretraining but not as the final architecture.

### 2. GoLLIE guideline-following (Sainz 2023)
- Role in pipeline: Decoder (text → structured output)
- Handles: Zero-shot structured extraction via natural language guidelines
- Fails at: Dialogue structure awareness — processes transcript as a flat text wall, losing speaker identity, round structure, and ritual signals
- Verdict: USEFUL AS DECODER ONLY. Its structured output mechanism can be adapted, but it cannot be the encoder because it destroys dialogue structure.

### 3. KnowCoder code-pretrained IE (Li 2024)
- Role in pipeline: Decoder (text → JSON)
- Handles: Best-in-class structured JSON output via code-pretrained LLM
- Fails at: Same dialogue structure blindness as GoLLIE; not dialogue-specific
- Verdict: USEFUL AS DECODER ONLY. The strongest choice for the output generation module, but needs an upstream dialogue encoder.

### 4. Longformer (Beltagy 2020)
- Role in pipeline: Token-level encoder (handles long text)
- Handles: 4096-token sequences efficiently via sliding window attention
- Fails at: Cannot generate output; produces embeddings only. No temporal convolution — treats all tokens equally regardless of their position in the dialogue timeline.
- Verdict: USEFUL AS TOKEN-LEVEL ENCODER. Good for the first stage (raw text → token embeddings), but the temporal modeling must come from a TCN layer above it.

### 5. GREAT graph neural network (Xu 2022, ACL)
- Role in pipeline: Cross-turn relation modeler
- Handles: Multi-hop reasoning across utterance nodes — elegant for modeling CHALLENGE edges, AGREE edges, etc.
- Fails at: No generation capability. Requires explicit graph construction from dialogue structure. Training data requirement: needs annotated utterance-level graphs.
- Verdict: USEFUL FOR SKILL BOUNDARY DETECTION. Could be an auxiliary module, but cannot be the primary architecture because it doesn't generate structured skill text.

### 6. TCN + Attention (Bai 2018 + our prior)
- Role in pipeline: Core temporal encoder
- Handles: Time-series modeling of utterance sequences; dilated convolutions for long-range dependency; cross-attention for skill-relevant focus
- Fails at: No generation capability — pure encoder
- Verdict: **SELECTED AS CORE ENCODER**. This is the only method that natively models Plaza discussion as what it fundamentally is: a temporal sequence of utterances. The dilated convolution structure maps perfectly to the multi-round structure of Plaza discussions.

## Selected Architecture: TCN-Skill-Extractor (TSE)

### Why TCN over other encoders?

1. **Plaza discussion IS a time series.** Unlike generic documents (2D grid) or static graphs, the fundamental structure of a discussion is a 1D temporal sequence. Convolution along this axis is the most natural operation. GNNs can model this too but require explicit graph construction; TCN does it implicitly through dilation.

2. **Dilated convolution matches Plaza's multi-round structure.** A Plaza discussion has 3-5 rounds, each 3-8 utterances. Important skill mentions may span across non-adjacent rounds. TCN's dilation pattern (d=1,2,4,...) grows the receptive field logarithmically — exactly as a round structure expands temporally.

3. **Cross-attention focuses on "skill moments."** Most utterances in a Plaza discussion are not skill-defining. The attention mechanism can learn to identify which specific utterances carry skill-relevant content. TF-IDF cannot distinguish "agent A proposes skill X" from "agent B complains about skill X not working" — but learned attention can.

4. **Existing TCN model is an asset, not baggage.** Our team has trained TCN-attention models before. This means: (a) known hyperparameter ranges, (b) known training pitfalls, (c) faster convergence. Starting from scratch with a GNN or a new transformer variant would add 2-3 months of debugging.

### Architecture Pipeline

```
Input: Plaza transcript D = {m_1, ..., m_N}
  Each m_i = {speaker_id, role, niche_role, ritual_signal, round_number, content}

Stage 1 — Token Encoding [Longformer or RoBERTa]:
  m_i.content → [CLS] w1 ... wk [SEP] → h_i ∈ R^768
  Append auxiliary embeddings: +speaker_embedding +signal_embedding +round_embedding

Stage 2 — TCN Temporal Modeling [Bai 2018 + DILATED convolutions]:
  3 dilated conv layers, kernel_size=3, dilations=(1,2,4)
  Receptive field: 1 + 2*(3-1)*(1+2+4) = 29 utterances
  Output: Z ∈ R^{N × d_tcn}

Stage 3 — Skill Query Cross-Attention [learnable probe vectors]:
  Q = {q_name, q_desc, q_category, q_tools, q_instr}  ← learnable parameters
  For each q_k:
    a_k = softmax(Z · q_k / sqrt(d_tcn))              ← attention over N utterances
    r_k = sum_i a_k[i] · Z[i]                         ← weighted pooling
  Output: R = {r_name, r_desc, r_category, r_tools, r_instr}

Stage 4 — Constrained JSON Decoder [CodeLLaMA-7B, QLoRA]:
  Input: concat(R) + brief context prefix
  Grammar-constrained beam search → valid JSON output
  Output: {"name": "...", "description": "...", "category": "...",
           "instructions": "...", "required_tools": [...]}
```

### Training Strategy

Phase 1 — Silver data generation:
- GPT-4 extracts skills from 50 seed Plaza transcripts → ~200-300 (transcript, skills) pairs
- Use a strict extraction guideline prompt that mirrors our SkillDefinition schema

Phase 2 — Human verification:
- Select 50 pairs for human review → gold evaluation set
- Correct field-level errors (wrong category, missing tools, vague instructions)

Phase 3 — Fine-tuning:
- Freeze Longformer token encoder (pretrained weights)
- Train TCN + Skill Query Attention + QLoRA CodeLLaMA decoder on silver data
- Evaluate on gold set

Phase 4 — Active learning:
- Identify high-loss examples → human annotate → add to training set
- Iterate 2-3 rounds

### Why NOT the alternative combinations

| Alternative | Rejection reason |
|-------------|-----------------|
| Pure GPT-4 zero-shot extraction | Not reproducible; closed-source; can't publish as a method contribution |
| Just Longformer + classification head | Can only classify "is there a skill?" → cannot generate instructions text |
| Just GoLLIE zero-shot (flat text → JSON) | Destroys dialogue structure — no speaker/round/signal awareness |
| GREAT GNN as primary encoder | No generation capability; requires manual graph construction per discussion |
| TCN + LSTM decoder | LSTM decoder quality is far below transformer decoder for long text generation |
| TCN + T5 decoder | T5 is not optimized for structured JSON output — hallucination rate would be high |

## Pre-specified Success Criteria

1. **Extraction precision at field level**: F1 ≥ 0.75 for each skill field (name, description, category, instructions, tools) when evaluated against human-verified extraction
2. **Structural validity**: ≥ 95% of extracted skill JSONs must be valid (parseable, all required fields present)
3. **Outperforms baselines**: TSE must outperform (a) TF-IDF + template baseline, (b) GPT-4 zero-shot prompt, and (c) GoLLIE flat-text zero-shot by ≥ 10% relative F1
4. **Ablation significance**: Removing TCN → significant F1 drop (≥ 8%); removing Skill Query Attention → significant F1 drop (≥ 5%); replacing CodeLLaMA decoder with T5 → validity rate drop (≥ 15%)
5. **Downstream utility**: Agents using TSE-extracted skills must achieve task success rate ≥ 80% of agents using human-written skills

## Key Risks

1. **Silver data quality**: If GPT-4 extraction quality is poor (≤ 60% precision on gold set), the fine-tuned TSE will inherit those errors. Mitigation: start with a small pilot (5 transcripts → 20 skills → human review) before generating the full 50-transcript corpus.
2. **TCN receptive field vs. discussion length**: If a single discussion exceeds 29 utterances (TCN receptive field), skill mentions at the very beginning may be missed. Mitigation: increase dilation to (1,2,4,8,16) for receptive field of 61, at the cost of deeper architecture.
3. **CodeLLaMA decoder hallucination**: Fine-tuned decoders may generate plausible but incorrect skill instructions. Mitigation: constrained decoding grammar + human evaluation of instructions quality.
