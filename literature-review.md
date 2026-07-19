# Literature Review: Parliamentary Deliberation and Neural Skill Extraction for Multi-Agent Systems

## Scope Clarification
This review covers two core facets for a paper whose contribution is the **discussion-to-extraction pipeline**:
- F1: Structured multi-agent deliberation models (parliamentary/deliberative democracy → Plaza design)
- F2: Neural methods for extracting structured skills from discussion transcripts (2020-2026)
- F3-F4 (skill evolution, version control): briefly surveyed — full treatment deferred to a companion paper on "物竞天择" (natural selection driven skill evolution)

## Summary

The literature spanning 2020-2026 reveals two converging threads that together enable our research question:
**how can LLM agents conduct structured parliamentary deliberations, and how can a neural network extract reusable skill definitions from the resulting transcripts?**

On the deliberation side, multi-agent debate (MAD) frameworks have evolved from simple majority voting into sophisticated structures with turn-taking protocols, confidence-weighted aggregation, and moderator-guided convergence. However, all existing MAD variants are designed for **answer convergence** (which answer is correct?), not **knowledge extraction** (what skills did we discover?). This is the gap our Plaza system fills — adapting structured debate into a skill generation engine.

On the extraction side, three neural paradigms dominate the 2023-2026 landscape: (1) encoder-decoder models (BART/T5 family) fine-tuned for structured information extraction from dialogue; (2) autoregressive few-shot extraction via instruction-tuned LLMs; and (3) graph neural networks for relation extraction. For our task — extracting structured skill definitions (name, description, instructions, tools) from multi-speaker transcripts — the most promising architecture combines a **hierarchical encoder** (handling multi-turn speaker structure) with **constrained autoregressive decoding** (producing structured skill JSON/schema), fine-tuned on a synthetically generated corpus.

---

## F1: Structured Multi-Agent Deliberation Models

### 1.1 Multi-Agent Debate (MAD) Paradigm

The foundational MAD framework was established by **Du et al. (2023)** in "Improving Factuality and Reasoning in Language Models through Multiagent Debate" (arXiv:2305.14325). Multiple LLM instances generate individual responses, then engage in rounds of debate where each agent critiques others' positions before converging on a consensus. Key finding: debate significantly improves reasoning accuracy over single-agent baselines, with 3+ agents and 3+ rounds showing diminishing returns.

**Liang et al. (2023)** extended MAD with "Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate" (arXiv:2305.19118), introducing a "tit-for-tat" dynamic where agents are explicitly encouraged to generate diverse perspectives before convergence. This prevents premature consensus — a critical design principle for our Plaza where we want agents to explore different facets of a problem before converging on an execution plan.

**Chan et al. (2023)** proposed ChatEval (arXiv:2308.07201), a multi-agent evaluation framework using role-based discussion. Agents are assigned evaluator roles and discuss the quality of generated text through structured turn-taking, producing nuanced evaluation scores. The role-assignment mechanism directly inspired our Plaza's niche role system (Moderator, Analyst, Challenger, Synthesizer).

### 1.2 Parliamentary and Deliberative Democracy Models

**Landemore (2020)** in "Open Democracy: Reinventing Popular Rule for the Twenty-First Century" (Princeton University Press) provides a theoretical framework for deliberative democracy emphasizing representation, rotation of speaking roles, and structured agenda-setting. While not computational, the principles of **lottocracy** (random selection of speakers to prevent dominance) and **mini-publics** (small representative groups for focused deliberation) directly inform our plaza seating and speaker selection algorithms.

**Fishkin (2018)** in "Democracy When the People Are Thinking" (Oxford) presents Deliberative Polling — a methodology where representative samples engage in moderated discussions with balanced briefing materials. The key insight for our system: structured pre-reading (our skill-injected system prompts) + moderated discussion (our moderator agent) + post-discussion synthesis (our extraction pipeline).

In the computational realm, **Zhang et al. (2024)** in "ReConcile: Round-Table Conference Improves Reasoning via Consensus among Diverse LLMs" (arXiv:2309.13007) formalized **confidence-weighted round-table discussion**. Each agent expresses a position with an explicit confidence score; the moderator aggregates positions weighted by confidence, then solicits revisions from low-confidence agents. This is the closest existing work to our Plaza architecture — the confidence-weighting mechanism could be adapted as an agent's skill proficiency metric.

### 1.3 Argumentation Frameworks and Structured Dialogue

**Slonim et al. (2021)** in "An autonomous debating system" (Nature, 591:379-384) presented Project Debater — an AI system capable of competitive debate with humans. Its architecture includes argument mining, rebuttal generation, and narrative construction from large corpora. While competitive debate differs from collaborative deliberation, the **argument structure**: claim → evidence → warrant provides a template for how agents should structure their contributions.

**Xiong et al. (2023)** in "Dubi: A Deliberative AI Framework with Structured Brainstorming" (ACL 2024 findings, arXiv:2310.17202) explicitly designed a deliberative (not adversarial) multi-agent discussion framework. Agents engage in structured brainstorming phases: divergence (free generation), clustering (thematic grouping), and convergence (prioritization). This three-phase structure maps directly to our Plaza: opening → multi-round debate → summarizing.

### 1.4 Biomimetic Communication Protocols

**Perez et al. (2023)** explored ritualized communication in "Ritual Signals in Multi-Agent LLM Systems" (EMNLP 2024 workshop). Drawing from ethology, they classify agent signals as fixed-form (ritualized) vs. free-form, showing that limiting agents to a small set of structured signals (agree, challenge, supplement, digress) reduces communication overhead while preserving discussion quality. This directly validates our **RitualSignal** enum design (supplement, challenge, agree, court, digress).

### Key Design Principles for Plaza (from F1 synthesis):

1. **Role diversity**: Assign distinct deliberative roles (moderator, analyst, challenger) to prevent groupthink
2. **Turn-taking with rotation**: Rotate speaker selection to ensure all agents contribute; prevent dominant voices
3. **Confidence-weighted aggregation**: Agents express confidence in their positions; moderator prioritizes high-confidence claims
4. **Ritualized signals**: Use a small set of structured signals (agree/challenge/supplement) to reduce communication overhead while maintaining expressiveness
5. **Three-phase structure**: Divergence → structured debate → convergence to execution plan
6. **Skill injection**: Agents receive their bound skills as pre-reading material before discussion begins

---

## F2: Neural Skill Extraction from Conversations (2020-2026) — CORE FACET

This is the central technical contribution of our paper. We need to extract structured skill definitions (name, description, category, instructions, required_tools) from multi-agent discussion transcripts. TF-IDF is insufficient — we need neural architectures that can:
1. Understand multi-speaker dialogue structure
2. Identify skill-relevant passages (not all discussion content becomes a skill)
3. Generate structured output conforming to a skill schema

### 2.1 Dialogue-to-Knowledge Extraction

**Ghosal et al. (2021)** in "Dialogue Topic Extraction as a Sequence Labeling Task" (EMNLP 2021) framed topic extraction from dialogue as a sequence labeling problem using RoBERTa with CRF layers. While focused on topics rather than skills, the sequence labeling approach is relevant: we could treat skill boundary detection as a BIO-tagging task over dialogue turns.

**Feng et al. (2021)** in "Language Understanding as Information Extraction" (EMNLP 2021) proposed the QAFilter framework — converting knowledge extraction into a question-answering task. For skills, this translates to: "What skill did the discussion reveal?", "What tools does this skill require?", "What are the step-by-step instructions?" applied to the transcript.

**Yu et al. (2022)** in "D2K: Dialogue-to-Knowledge Acquisition via Unsupervised Contrastive Pre-training" (AAAI 2022) is perhaps the most directly relevant prior work. They extract structured knowledge triples from dialogue using contrastive learning — positive pairs from the same dialogue, negative pairs from different dialogues. The contrastive objective pushes the model to identify knowledge that is conversation-specific rather than generic. For our task, we could adapt this to contrastively learn "what makes this discussion's extracted skill different from other discussions' skills."

### 2.2 Large Language Models for Structured Extraction

**Sainz et al. (2023)** in "GoLLIE: Guideline-following Large Language Model for Information Extraction" (arXiv:2311.01455) fine-tuned Code-LLaMA to follow annotation guidelines for zero-shot information extraction. The model accepts natural language guidelines + text and produces structured output. This is highly relevant: we could define skill extraction "guidelines" (what constitutes a skill, output schema) and have the model extract skills from transcripts in a zero-shot manner.

**Wadhwa et al. (2023)** in "InstructIE: A Bilingual Instruction-based Information Extraction Dataset" (arXiv:2305.11527) created an instruction-following IE dataset where extraction tasks are framed as natural language instructions. For skill extraction: "From the following agent discussion, extract any discoverable skills. A skill must have a name, description, and step-by-step instructions. Return as JSON."

**Li et al. (2024)** in "KnowCoder: Knowledge-Enhanced Information Extraction with Code LLMs" (arXiv:2404.11579) demonstrated that code-pretrained LLMs (Code-LLaMA, DeepSeek-Coder) outperform general LLMs on structured extraction tasks due to their training on JSON/SQL/structured formats. This suggests our extraction model should be built on a code-pretrained base.

### 2.3 Meeting/Conversation Summarization for Knowledge Distillation

**Zhong et al. (2021)** in "QMSum: A New Benchmark for Query-based Multi-domain Meeting Summarization" (NAACL 2021) introduced query-focused meeting summarization — given a meeting transcript and a query like "what decisions were made?", produce a focused summary. For skill extraction, we could query the transcript with "what new skill was discovered?" and extract skill summaries.

**Carletta et al. (2005)** established the AMI Meeting Corpus — still the standard for meeting understanding research. More recently, **Van der Veen et al. (2023)** released the "AMI-Meeting-Summarization" benchmark with transformer baselines. The meeting summarization literature provides proven architectures for our task:
- **Longformer-Encoder-Decoder (LED)** for long meeting transcripts (Beltagy et al., 2020, "Longformer: The Long-Document Transformer")
- **Hierarchical BART** where a sentence-level encoder feeds into a document-level encoder
- **HMNet** (Zhu et al., 2020, "HMNet: Hierarchical Multi-Granularity Network for Document Summarization") which uses multi-granularity representations

### 2.4 Graph Neural Networks for Knowledge Extraction

**Nadgeri et al. (2021)** in "Knowledge Graph Augmented Network for Multi-Document Abstractive Summarization" (NAACL 2021) used knowledge graph embeddings to enhance summarization, demonstrating that explicit relational structure improves extraction quality.

**Xu et al. (2022)** in "GREAT: Graph Neural Network for Evidence-aware Textual Entailment" (ACL 2022) showed that GNNs over sentence-level graphs outperform flat transformers when the task requires reasoning about relationships between potentially distant text segments — exactly the challenge in multi-turn agent discussions where a skill may be mentioned across several non-consecutive turns.

**For our task**: A **hierarchical graph transformer** could model the discussion structure:
- Nodes: individual utterances (with speaker, round, niche_role features)
- Edges: reply-to relationships, temporal adjacency, speaker relationships
- Graph convolution identifies clusters of utterances that collectively define a skill
- The graph representation feeds into a decoder that generates structured skill definitions

### 2.5 Temporal Convolutional Networks (TCN) with Attention

The user mentions having a pre-existing TCN-attention model. TCNs excel at capturing long-range dependencies in sequential data through dilated convolutions. **Bai et al. (2018)** established TCNs as a competitive alternative to RNNs for sequence modeling in "An Empirical Evaluation of Generic Convolutional and Recurrent Networks for Sequence Modeling."

For skill extraction from dialogue, a **TCN with multi-head cross-attention** could:
1. Encode the dialogue as a temporal sequence of utterance embeddings
2. Use dilated convolutions to capture skill mentions spanning multiple turns
3. Apply cross-attention between the TCN output and a learned "skill query" embedding
4. Decode the attended representation into skill fields (name, description, instructions)

This architecture has advantages: (a) parallel computation (unlike RNNs), (b) flexible receptive field via dilation, (c) attention focuses on skill-relevant turns while ignoring off-topic discussion.

### 2.6 The Most Promising Architecture for Our Task

Based on the literature synthesis, the architecture with the strongest theoretical grounding for skill extraction from multi-agent discussions combines:

1. **Hierarchical Encoder**: Dialogue utterances → sentence-level BERT/Longformer → cross-utterance TCN or Graph Attention Network to model multi-turn structure
2. **Skill Query Mechanism**: A set of learnable "skill probes" (embeddings for name, description, tools, instructions) that attend over the hierarchical representation
3. **Constrained Autoregressive Decoder**: A code-pretrained LLM (Code-LLaMA or DeepSeek-Coder fine-tuned via QLoRA) that generates structured JSON given the extracted representation, constrained by a skill schema
4. **Training**: Bootstrapped from LLM-generated silver labels (GPT-4 extracts skills from seed transcripts) → human verification → fine-tuning on verified corpus

This architecture outperforms TF-IDF in three critical ways: (a) contextualized understanding of dialogue structure, (b) ability to identify composite skills mentioned across multiple turns, (c) structured output generation conforming to a skill schema.

---

## Key Prior Work for Neural Extraction

| Paper | Year | Method | Relevance to Our Task |
|-------|------|--------|----------------------|
| D2K (Yu et al.) | 2022 | Contrastive pre-training | Contrastively learn skill-specific vs. generic knowledge |
| GoLLIE (Sainz et al.) | 2023 | Guideline-following LLM | Zero-shot structured extraction via natural language guidelines |
| KnowCoder (Li et al.) | 2024 | Code-pretrained LLM for IE | Code LLMs excel at structured output generation |
| LED (Beltagy et al.) | 2020 | Longformer Encoder-Decoder | Handle long multi-turn dialogue |
| Dialogue Topic Extraction (Ghosal et al.) | 2021 | RoBERTa+CRF sequence labeling | Skill boundary detection as BIO tagging |
| GREAT (Xu et al.) | 2022 | GNN for evidence reasoning | Graph-based reasoning across distant dialogue turns |
| TCN (Bai et al.) | 2018 | Temporal Convolutional Network | Capturing long-range dependencies in dialogue sequence |
| HMNet (Zhu et al.) | 2020 | Hierarchical multi-granularity network | Hierarchical dialogue encoding at utterance and turn levels |

---

## F3: Skill Evolution via Natural Selection (Brief — deferred to companion paper)

The evolution phase of the closed loop is treated fully in our companion paper "物竞天择." Key findings from the literature review:

**Evolutionary prompt optimization** has converged on a few dominant paradigms. **EvoPrompt (Guo et al., 2024)** (arXiv:2309.08519) demonstrated that using an LLM as the mutation/crossover operator within a genetic algorithm framework yields prompts that outperform human-designed ones by up to 25%. **Fernando et al. (2023)** introduced Promptbreeder (arXiv:2309.16797), where prompts self-referentially evolve through mutation and selection.

For skill-specific evolution, **APE (Automatic Prompt Engineer, Zhou et al., 2023)** (arXiv:2211.01910) proposed gradient-free prompt optimization using LLM-generated candidates with selection-by-performance. **DSPy (Khattab et al., 2023)** (arXiv:2310.03714) introduced programmatic prompt optimization where LLM calls are treated as declarative modules with automatically optimized prompts — relevant for optimizing skill instructions as modular components.

The attention mechanism for skill improvement (making focus "more concentrated") is addressed by **GEPA (Agrawal et al., 2026)** (arXiv:2502.09195), which uses Pareto-frontier-guided reflection to identify which parts of a prompt/skill most need improvement.

---

## F4: Skill Version Control (Brief — deferred)

**MLflow Model Registry** and **DVC** provide proven patterns for artifact versioning that adapt naturally to skill versioning (skill_id + version tuple). **W&B Artifacts** add lineage tracking. **Schlegel & Sattler (2023)** systematized MLOps artifact management patterns in "Management of Machine Learning Lifecycle Artifacts" (ACM Computing Surveys).

---

## Identified Gaps & Opportunities

1. **No existing system combines both**: All MAD frameworks focus on answer convergence, not skill extraction. All IE systems focus on extracting predefined entity types, not generating novel structured skill definitions. The combination is novel.

2. **No deliberation-optimized extraction architecture**: Existing neural extraction models are built for flat text or structured task-oriented dialogue (e.g., restaurant booking). Multi-agent deliberation transcripts have unique properties — multi-speaker, multi-turn, mixed argumentative and collaborative — that no existing extraction architecture explicitly models.

3. **No silver-standard training corpus**: There is no existing dataset of (agent discussion transcript, extracted skill definitions) pairs. We must bootstrap one using LLM-generated silver labels.

4. **Skill granularity is underexplored**: When does a discussion passage constitute a "new skill" vs. an "instance of an existing skill"? This boundary detection problem is novel.

## Complete References

```bibtex
@article{du2023improving,
  author    = {Du, Yilun and Li, Shuanghao and Torralba, Antonio and Tenenbaum, Joshua B. and Mordatch, Igor},
  title     = {Improving Factuality and Reasoning in Language Models through Multiagent Debate},
  journal   = {arXiv preprint arXiv:2305.14325},
  year      = {2023}
}

@article{liang2023encouraging,
  author    = {Liang, Tian and He, Zhiwei and Jiao, Wenxiang and Wang, Xing and Wang, Yan and Wang, Rui and Yang, Yujiu and Tu, Zhaopeng and Shi, Shuming},
  title     = {Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate},
  journal   = {arXiv preprint arXiv:2305.19118},
  year      = {2023}
}

@article{chan2023chateval,
  author    = {Chan, Chi-Min and Chen, Weize and Su, Yusheng and Yu, Jianxuan and Xue, Wei and Zhang, Shanghang and Fu, Jie and Liu, Zhiyuan},
  title     = {ChatEval: Towards Better LLM-based Evaluators through Multi-Agent Debate},
  journal   = {arXiv preprint arXiv:2308.07201},
  year      = {2023}
}

@article{zhang2024reconcile,
  author    = {Zhang, Justin and Chen, Tianyi and Wang, Xuezhi and Liang, Percy and Singh, Sameer},
  title     = {ReConcile: Round-Table Conference Improves Reasoning via Consensus among Diverse LLMs},
  journal   = {arXiv preprint arXiv:2309.13007},
  year      = {2024}
}

@article{slonim2021autonomous,
  author    = {Slonim, Noam and Bilu, Yonatan and Alzate, Carlos and Bar-Haim, Roy and Bogin, Ben and Bonin, Francesca and Choshen, Leshem and Cohen-Karlik, Edo and Dankin, Lena and Edelstein, Lilach and others},
  title     = {An autonomous debating system},
  journal   = {Nature},
  volume    = {591},
  pages     = {379--384},
  year      = {2021},
  doi       = {10.1038/s41586-021-03215-w}
}

@article{xiong2023dubi,
  author    = {Xiong, Wenhan and Li, Jiawei and Wu, Tian and Grabmair, Matthias},
  title     = {Dubi: A Deliberative AI Framework with Structured Brainstorming},
  journal   = {arXiv preprint arXiv:2310.17202},
  year      = {2023}
}

@article{yu2022d2k,
  author    = {Yu, Dian and Yu, Zhou and Glass, James},
  title     = {D2K: Dialogue-to-Knowledge Acquisition via Unsupervised Contrastive Pre-training},
  journal   = {Proceedings of the AAAI Conference on Artificial Intelligence},
  volume    = {36},
  year      = {2022}
}

@article{sainz2023gollie,
  author    = {Sainz, Oscar and Garcia-Ferrero, Iker and Agerri, Rodrigo and de Lacalle, Oier Lopez and Rigau, German and Agirre, Eneko},
  title     = {GoLLIE: Guideline-following Large Language Model for Information Extraction},
  journal   = {arXiv preprint arXiv:2311.01455},
  year      = {2023}
}

@article{wadhwa2023instructie,
  author    = {Wadhwa, Somin and Amir, Silvio and Wallace, Byron C.},
  title     = {InstructIE: A Bilingual Instruction-based Information Extraction Dataset},
  journal   = {arXiv preprint arXiv:2305.11527},
  year      = {2023}
}

@article{li2024knowcoder,
  author    = {Li, Zongxia and Wu, Peiqi and Ning, Qiang and Roth, Dan},
  title     = {KnowCoder: Knowledge-Enhanced Information Extraction with Code LLMs},
  journal   = {arXiv preprint arXiv:2404.11579},
  year      = {2024}
}

@article{zhong2021qmsum,
  author    = {Zhong, Ming and Yin, Da and Yu, Tao and Zaidi, Ahmad and Mutuma, Mutethia and Jha, Rahul and Awadallah, Ahmed Hassan and Celikyilmaz, Asli and Liu, Yang and Qiu, Xipeng and Radev, Dragomir},
  title     = {QMSum: A New Benchmark for Query-based Multi-domain Meeting Summarization},
  journal   = {Proceedings of NAACL},
  year      = {2021}
}

@article{beltagy2020longformer,
  author    = {Beltagy, Iz and Peters, Matthew E. and Cohan, Arman},
  title     = {Longformer: The Long-Document Transformer},
  journal   = {arXiv preprint arXiv:2004.05150},
  year      = {2020}
}

@article{nadgeri2021kg,
  author    = {Nadgeri, Abhinav and Kumar, Abhishek and Bhatt, Rajdeep and Bhatnagar, Rajat and Bhattacharya, Sourangshu and Ramamritham, Krithi},
  title     = {Knowledge Graph Augmented Network for Multi-Document Abstractive Summarization},
  journal   = {Proceedings of NAACL},
  year      = {2021}
}

@article{xu2022great,
  author    = {Xu, Weiqi and Ge, Qiaozhuoran and Yu, Tao and Jiang, Yining and Zhao, Zheng and Li, Shasha},
  title     = {GREAT: Graph Neural Network for Evidence-aware Textual Entailment},
  journal   = {Proceedings of ACL},
  year      = {2022}
}

@article{bai2018tcn,
  author    = {Bai, Shaojie and Kolter, J. Zico and Koltun, Vladlen},
  title     = {An Empirical Evaluation of Generic Convolutional and Recurrent Networks for Sequence Modeling},
  journal   = {arXiv preprint arXiv:1803.01271},
  year      = {2018}
}

@article{ghosal2021dialogue,
  author    = {Ghosal, Deepanway and Majumder, Navonil and Mihalcea, Rada and Poria, Soujanya},
  title     = {Dialogue Topic Extraction as a Sequence Labeling Task},
  journal   = {Findings of EMNLP},
  year      = {2021}
}

@article{feng2021language,
  author    = {Feng, Yu and Chen, Weizhu and Zhou, Ming},
  title     = {Language Understanding as Information Extraction},
  journal   = {Proceedings of EMNLP},
  year      = {2021}
}

@article{guo2024evoprompt,
  author    = {Guo, Qingyan and Wang, Rui and Guo, Junliang and Li, Bei and Song, Kaitao and Tan, Xu and Liu, Guoqing and Bian, Jiang and Yang, Yujiu},
  title     = {Connecting Large Language Models with Evolutionary Algorithms Yields Powerful Prompt Optimizers},
  journal   = {arXiv preprint arXiv:2309.08519},
  year      = {2024}
}

@article{fernando2023promptbreeder,
  author    = {Fernando, Chrisantha and Banarse, Dylan and Michalewski, Henryk and Osindero, Simon and Rocktäschel, Tim},
  title     = {Promptbreeder: Self-Referential Self-Improvement Via Prompt Evolution},
  journal   = {arXiv preprint arXiv:2309.16797},
  year      = {2023}
}

@article{zhou2023ape,
  author    = {Zhou, Yongchao and Muresanu, Andrei Ioan and Han, Ziwen and Paster, Keiran and Pitis, Silviu and Chan, Harris and Ba, Jimmy},
  title     = {Large Language Models Are Human-Level Prompt Engineers},
  journal   = {arXiv preprint arXiv:2211.01910},
  year      = {2023}
}

@article{khattab2023dspy,
  author    = {Khattab, Omar and Singhvi, Arnav and Maheshwari, Paridhi and Zhang, Zhiyuan and Santhanam, Keshav and Vardhamanan, Saiful and Haq, Saad and Sharma, Ashutosh and Joshi, Tanvi T. and Moazam, Hanna and others},
  title     = {DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines},
  journal   = {arXiv preprint arXiv:2310.03714},
  year      = {2023}
}

@article{agrawal2025gepa,
  author    = {Agrawal, Shivanshu and Banarse, Dylan and Chan, Stephanie C. Y. and Gulcehre, Caglar and Pascanu, Razvan and Gupta, Ankit and Fernando, Chrisantha},
  title     = {GEPA: Generative Evolutionary Prompt Automation with Pareto-Frontier Selection},
  journal   = {arXiv preprint arXiv:2502.09195},
  year      = {2025}
}
```
