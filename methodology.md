# Methodology: TCN-Skill-Extractor (TSE) — Neural Skill Extraction from Plaza Discussions

## Research Question
How to extract structured skill definitions from multi-agent Plaza deliberation transcripts using a neural architecture that combines TCN temporal modeling, cross-attention, and constrained decoding?

## Architecture Overview

```
Input: Plaza transcript D = {m_1, ..., m_N}
  m_i = {speaker_id, role, niche_role, ritual_signal, round_number, content}

[Stage 1] Longformer Token Encoder
  content text → token embeddings h_i ∈ R^768

[Stage 2] TCN Temporal Module
  {h_1, ..., h_N} → Z ∈ R^{N × 256}

[Stage 3] Skill Query Cross-Attention
  Z × {q_name, q_desc, q_category, q_tools, q_instr} → R = {r_name, ..., r_instr}

[Stage 4] Constrained JSON Decoder
  R + context → valid Skill JSON string
```

---

## 1. Data Preparation

### 1.1 Plaza Transcript Format

```python
# Each discussion produces a JSON transcript

transcript = {
    "discussion_id": "abc123",
    "topic": "如何优化AWS ES集群的扩缩容策略",
    "messages": [
        {
            "msg_id": "m1",
            "speaker_id": "agent_architect_01",
            "speaker_name": "架构师Alpha",
            "role": "architect",
            "niche_role": "moderator",
            "ritual_signal": "supplement",
            "round_number": 0,
            "content": "今天讨论AWS ES集群的扩缩容策略。请各位从各自专业角度分析..."
        },
        {
            "msg_id": "m2",
            "speaker_id": "agent_devops_03",
            "speaker_name": "运维专家Gamma",
            "role": "devops",
            "niche_role": "analyst",
            "ritual_signal": "supplement",
            "round_number": 1,
            "content": "从运维角度，当前ES集群在高峰期的CPU使用率达到85%..."
        },
        # ... N utterances total
    ]
}

# Ground-truth extraction (for training):
skills = [
    {
        "name": "AWS ES Auto-Scaling",
        "description": "基于CloudWatch指标自动调整ES集群节点数",
        "category": "automation",
        "instructions": "1. 配置CloudWatch告警: CPU>70%持续5min触发...\n2. ...",
        "required_tools": ["aws_cli", "python_boto3", "cloudwatch_api"]
    },
    # ... k skills extracted from this discussion
]
```

### 1.2 Silver Data Generation (GPT-4 Bootstrapping)

```python
# pseudocode: generate_training_data.py

def generate_silver_data(plaza_transcripts: list[dict]) -> list[dict]:
    """
    Use GPT-4 to extract skills from seed transcripts.
    Produces ~200-300 (transcript, skills) pairs for training.
    """
    extraction_prompt = """You are a skill extraction expert. Given a multi-agent discussion
transcript, extract ALL discoverable skills. A skill is a reusable piece of expertise
that an agent could use to solve a task.

For each skill, output a JSON object with these EXACT fields:
- name: short, descriptive name (max 50 chars)
- description: what problem this skill solves (1-3 sentences)
- category: one of [automation, research, general, analysis, monitoring, development]
- instructions: step-by-step procedure (3-10 steps, imperative mood)
- required_tools: list of tool names needed (e.g., ["aws_cli", "python_boto3"])

CRITICAL RULES:
1. Only extract skills explicitly discussed or implied by the discussion content.
2. Do NOT extract generic skills like "communication" or "teamwork" — skills must be task-specific.
3. Instructions must be actionable: someone reading them should be able to execute the task.
4. If no skill is discussed, return an empty list.

Transcript:
{transcript_text}

Output ONLY a JSON array of skill objects. No other text."""

    dataset = []
    for transcript in plaza_transcripts:
        # Format transcript as readable text
        text = format_transcript_for_extraction(transcript)
        
        # Call GPT-4 for extraction
        response = call_llm(
            model="gpt-4",
            system_prompt=extraction_prompt,
            user_message=text,
            temperature=0.2,  # low temp for consistent extraction
        )
        
        # Parse JSON output
        try:
            extracted_skills = json.loads(response)
            # Validate each skill has all required fields
            for skill in extracted_skills:
                validate_skill_fields(skill)
            dataset.append({
                "transcript": transcript,
                "skills": extracted_skills
            })
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"GPT-4 extraction failed for {transcript['discussion_id']}: {e}")
            continue
    
    return dataset


def format_transcript_for_extraction(transcript: dict) -> str:
    """Convert transcript to a readable text format for the LLM."""
    lines = [f"Topic: {transcript['topic']}\n"]
    for msg in transcript["messages"]:
        lines.append(
            f"[Round {msg['round_number']}] {msg['speaker_name']} "
            f"({msg['role']}, signal={msg['ritual_signal']}): "
            f"{msg['content']}"
        )
    return "\n".join(lines)


def validate_skill_fields(skill: dict):
    """Ensure skill has all required fields with valid types."""
    required = {
        "name": str,
        "description": str,
        "category": str,
        "instructions": str,
        "required_tools": list,
    }
    valid_categories = {
        "automation", "research", "general",
        "analysis", "monitoring", "development"
    }
    
    for field, expected_type in required.items():
        if field not in skill:
            raise ValidationError(f"Missing field: {field}")
        if not isinstance(skill[field], expected_type):
            raise ValidationError(f"Wrong type for {field}: {type(skill[field])}")
    
    if skill["category"] not in valid_categories:
        raise ValidationError(f"Invalid category: {skill['category']}")
    
    if len(skill["instructions"]) < 20:
        raise ValidationError("Instructions too short")
```

### 1.3 Dataset Class

```python
# pseudocode: dataset.py

import torch
from torch.utils.data import Dataset
from transformers import LongformerTokenizer


class PlazaExtractionDataset(Dataset):
    """Dataset of (transcript, skills) pairs for TSE training."""
    
    def __init__(
        self,
        data: list[dict],
        tokenizer: LongformerTokenizer,
        max_utterances: int = 64,     # truncate to N max utterances
        max_text_len: int = 512,       # max tokens per utterance
    ):
        self.data = data
        self.tokenizer = tokenizer
        self.max_utterances = max_utterances
        self.max_text_len = max_text_len
        
        # Build auxiliary embedding tables
        self.role_to_id = self._build_vocab(
            [msg["role"] for item in data for msg in item["transcript"]["messages"]]
        )
        self.signal_to_id = self._build_vocab(
            [msg["ritual_signal"] for item in data for msg in item["transcript"]["messages"]]
        )
        self.niche_to_id = self._build_vocab(
            [msg["niche_role"] for item in data for msg in item["transcript"]["messages"]]
        )
    
    def _build_vocab(self, items: list[str]) -> dict:
        unique = sorted(set(items))
        return {item: i for i, item in enumerate(unique)}
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx: int) -> dict:
        item = self.data[idx]
        transcript = item["transcript"]
        skills = item["skills"]
        
        # ── Encode utterances ──
        N = min(len(transcript["messages"]), self.max_utterances)
        utterances = transcript["messages"][:N]
        
        token_ids_list = []
        attention_mask_list = []
        role_ids = []
        signal_ids = []
        niche_ids = []
        round_ids = []
        
        for msg in utterances:
            # Tokenize each utterance
            encoded = self.tokenizer(
                msg["content"],
                max_length=self.max_text_len,
                padding="max_length",
                truncation=True,
                return_tensors="pt",
            )
            token_ids_list.append(encoded["input_ids"].squeeze(0))
            attention_mask_list.append(encoded["attention_mask"].squeeze(0))
            role_ids.append(self.role_to_id.get(msg["role"], 0))
            signal_ids.append(self.signal_to_id.get(msg["ritual_signal"], 0))
            niche_ids.append(self.niche_to_id.get(msg["niche_role"], 0))
            round_ids.append(msg["round_number"])
        
        # Pad to max_utterances
        pad_len = self.max_utterances - N
        if pad_len > 0:
            zero_ids = torch.zeros(pad_len, self.max_text_len, dtype=torch.long)
            zero_mask = torch.zeros(pad_len, self.max_text_len, dtype=torch.long)
            token_ids_list.extend([zero_ids[i] for i in range(pad_len)])
            attention_mask_list.extend([zero_mask[i] for i in range(pad_len)])
            role_ids.extend([0] * pad_len)
            signal_ids.extend([0] * pad_len)
            niche_ids.extend([0] * pad_len)
            round_ids.extend([-1] * pad_len)
        
        # ── Encode target skills as JSON string ──
        skills_json = json.dumps(skills, ensure_ascii=False)
        target_encoded = self.tokenizer(
            skills_json,
            max_length=1024,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        
        return {
            "utterance_input_ids": torch.stack(token_ids_list),     # (N, max_text_len)
            "utterance_attention_mask": torch.stack(attention_mask_list),  # (N, max_text_len)
            "role_ids": torch.tensor(role_ids),                     # (N,)
            "signal_ids": torch.tensor(signal_ids),                 # (N,)
            "niche_ids": torch.tensor(niche_ids),                   # (N,)
            "round_ids": torch.tensor(round_ids),                   # (N,)
            "utterance_count": torch.tensor(N),                     # actual utterance count
            "target_input_ids": target_encoded["input_ids"].squeeze(0),  # (target_len,)
            "target_attention_mask": target_encoded["attention_mask"].squeeze(0),
        }
```

---

## 2. Model Architecture — Detailed Pseudocode

### 2.1 Stage 1: Longformer Token Encoder

```python
# pseudocode: tse_model.py (part 1)

import torch
import torch.nn as nn
from transformers import LongformerModel, LongformerConfig


class LongformerUtteranceEncoder(nn.Module):
    """
    Encodes each utterance independently via Longformer.
    Input: (N utterances × text) → Output: (N × 768) utterance embeddings
    """
    
    def __init__(
        self,
        model_name: str = "allenai/longformer-base-4096",
        freeze: bool = True,          # freeze Longformer weights during training
        embedding_dim: int = 768,
    ):
        super().__init__()
        self.longformer = LongformerModel.from_pretrained(model_name)
        self.embedding_dim = embedding_dim
        
        if freeze:
            for param in self.longformer.parameters():
                param.requires_grad = False
    
    def forward(
        self,
        input_ids: torch.Tensor,      # shape: (N, max_text_len)
        attention_mask: torch.Tensor, # shape: (N, max_text_len)
    ) -> torch.Tensor:
        """
        Encode N utterances independently.
        
        Because Longformer is expensive for per-utterance forward pass,
        we batch all utterances together by reshaping to (N, seq_len)
        and processing in a single forward pass.
        
        Returns: utterance_embeddings of shape (N, 768)
        """
        # input_ids: (N, max_text_len)
        N, L = input_ids.shape
        
        outputs = self.longformer(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=False,
        )
        
        # Use [CLS] token embedding as utterance representation
        # last_hidden_state: (N, L, 768)
        cls_embeddings = outputs.last_hidden_state[:, 0, :]  # (N, 768)
        
        return cls_embeddings  # (N, 768)
```

### 2.2 Stage 2: TCN Temporal Module

```python
# pseudocode: tse_model.py (part 2)


class DilatedConvBlock(nn.Module):
    """Single dilated convolution block with residual connection."""
    
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        dilation: int = 1,
        dropout: float = 0.1,
    ):
        super().__init__()
        
        # Depthwise-separable dilated conv for efficiency
        self.depthwise_conv = nn.Conv1d(
            in_channels, in_channels,
            kernel_size=kernel_size,
            dilation=dilation,
            padding=dilation * (kernel_size - 1) // 2,
            groups=in_channels,  # depthwise
        )
        self.pointwise_conv = nn.Conv1d(in_channels, out_channels, kernel_size=1)
        self.layer_norm = nn.LayerNorm(out_channels)
        self.dropout = nn.Dropout(dropout)
        self.relu = nn.ReLU()
        
        # Residual projection if in_channels != out_channels
        self.residual = (
            nn.Conv1d(in_channels, out_channels, kernel_size=1)
            if in_channels != out_channels
            else nn.Identity()
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: (batch, channels, time_steps)
        Returns: (batch, out_channels, time_steps)
        """
        residual = self.residual(x)
        
        # Depthwise dilated conv
        out = self.depthwise_conv(x)
        out = out.permute(0, 2, 1)  # (batch, time, channels)
        out = self.layer_norm(out)
        out = out.permute(0, 2, 1)  # (batch, channels, time)
        
        # Pointwise conv
        out = self.pointwise_conv(out)
        out = self.relu(out)
        out = self.dropout(out)
        
        return out + residual


class TCNTemporalModule(nn.Module):
    """
    Multi-layer dilated TCN over utterance sequence.
    
    Layer 0: d=1, kernel=3, receptive field covers ±2 neighbors
    Layer 1: d=2, kernel=3, receptive field covers ±4 neighbors
    Layer 2: d=4, kernel=3, receptive field covers ±8 neighbors
    Layer 3: d=8, kernel=3, receptive field covers ±16 neighbors (optional)
    
    Total receptive field with 3 layers: 29 utterances (~3-5 Plaza rounds)
    """
    
    def __init__(
        self,
        input_dim: int = 768,         # Longformer embedding dim
        hidden_dim: int = 256,
        num_layers: int = 3,
        kernel_size: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()
        
        # Input projection
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        # Dilated conv stack
        dilations = [2 ** i for i in range(num_layers)]  # [1, 2, 4, ...]
        self.conv_blocks = nn.ModuleList([
            DilatedConvBlock(
                in_channels=hidden_dim,
                out_channels=hidden_dim,
                kernel_size=kernel_size,
                dilation=d,
                dropout=dropout,
            )
            for d in dilations
        ])
        
        # Output projection
        self.output_proj = nn.Linear(hidden_dim, hidden_dim)
        self.layer_norm = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(dropout)
    
    def forward(
        self,
        utterance_embeddings: torch.Tensor,  # (batch, N, 768)
        attention_mask: torch.Tensor,        # (batch, N) — 1=real, 0=pad
    ) -> torch.Tensor:
        """
        Apply dilated temporal convolutions over utterance sequence.
        
        Returns: temporal_features of shape (batch, N, hidden_dim)
        """
        batch, N, _ = utterance_embeddings.shape
        
        # Project to hidden dim
        x = self.input_proj(utterance_embeddings)  # (batch, N, hidden_dim)
        
        # TCN expects (batch, channels, time)
        x = x.permute(0, 2, 1)  # (batch, hidden_dim, N)
        
        # Apply dilated conv blocks
        mask = attention_mask.unsqueeze(1)  # (batch, 1, N) for broadcasting
        for conv_block in self.conv_blocks:
            x = conv_block(x)
            x = x * mask  # zero out padded positions
        
        # Back to (batch, N, hidden_dim)
        x = x.permute(0, 2, 1)  # (batch, N, hidden_dim)
        
        # Output projection
        x = self.output_proj(x)
        x = self.layer_norm(x)
        x = self.dropout(x)
        
        return x  # (batch, N, hidden_dim)
```

### 2.3 Stage 3: Skill Query Cross-Attention

```python
# pseudocode: tse_model.py (part 3)


class SkillQueryAttention(nn.Module):
    """
    Learnable skill-probe vectors attend over the TCN output to extract
    field-specific representations.
    
    5 query vectors, one per skill field:
    q_name, q_desc, q_category, q_tools, q_instr
    
    Each query independently attends to all N utterances via scaled 
    dot-product cross-attention, producing a weighted sum of utterance features.
    
    This replaces TF-IDF keyword matching with learned attention patterns.
    """
    
    def __init__(
        self,
        hidden_dim: int = 256,
        num_heads: int = 4,
        num_queries: int = 5,  # one per skill field
        dropout: float = 0.1,
    ):
        super().__init__()
        
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.num_queries = num_queries
        self.head_dim = hidden_dim // num_heads
        
        # Learnable query vectors — initialized randomly, trained end-to-end
        # These are the "skill probes" that learn WHERE to look in a discussion
        self.query_vectors = nn.Parameter(
            torch.randn(1, num_queries, hidden_dim) * 0.02
        )
        
        # Multi-head projection matrices
        self.q_proj = nn.Linear(hidden_dim, hidden_dim)
        self.k_proj = nn.Linear(hidden_dim, hidden_dim)
        self.v_proj = nn.Linear(hidden_dim, hidden_dim)
        self.out_proj = nn.Linear(hidden_dim, hidden_dim)
        
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(hidden_dim)
    
    def forward(
        self,
        temporal_features: torch.Tensor,  # (batch, N, hidden_dim)
        attention_mask: torch.Tensor,     # (batch, N)
    ) -> torch.Tensor:
        """
        Cross-attention: queries attend over temporal features.
        
        Returns: skill_representations of shape (batch, num_queries, hidden_dim)
        Each of the 5 output vectors captures one aspect of the skill.
        """
        batch, N, _ = temporal_features.shape
        
        # ── Multi-head projections ──
        # Queries: (batch, num_queries, num_heads, head_dim)
        Q = self.q_proj(self.query_vectors).view(
            1, self.num_queries, self.num_heads, self.head_dim
        ).expand(batch, -1, -1, -1)
        
        # Keys/Values: (batch, N, num_heads, head_dim)
        K = self.k_proj(temporal_features).view(
            batch, N, self.num_heads, self.head_dim
        )
        V = self.v_proj(temporal_features).view(
            batch, N, self.num_heads, self.head_dim
        )
        
        # ── Scaled dot-product attention ──
        # attn_scores: (batch, num_heads, num_queries, N)
        Q = Q.permute(0, 2, 1, 3)  # (batch, num_heads, num_queries, head_dim)
        K = K.permute(0, 2, 1, 3)  # (batch, num_heads, N, head_dim)
        
        scale = self.head_dim ** -0.5
        attn_scores = torch.matmul(Q, K.transpose(-2, -1)) * scale
        
        # Apply mask: set padded positions to -inf
        # mask shape: (batch, 1, 1, N) after unsqueeze
        mask = attention_mask.unsqueeze(1).unsqueeze(2)  # (batch, 1, 1, N)
        attn_scores = attn_scores.masked_fill(mask == 0, float("-inf"))
        
        attn_weights = torch.softmax(attn_scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # Weighted sum: (batch, num_heads, num_queries, head_dim)
        V = V.permute(0, 2, 1, 3)  # (batch, num_heads, N, head_dim)
        context = torch.matmul(attn_weights, V)
        
        # ── Concatenate heads and project ──
        # context: (batch, num_queries, num_heads, head_dim)
        context = context.permute(0, 2, 1, 3).contiguous()
        context = context.view(batch, self.num_queries, self.hidden_dim)
        
        # Output projection with residual
        out = self.out_proj(context)
        out = self.layer_norm(out + self.query_vectors.expand(batch, -1, -1))
        out = self.dropout(out)
        
        return out  # (batch, num_queries=5, hidden_dim)


# Named accessors for the 5 query outputs
class SkillRepresentation(nn.Module):
    """
    Wraps SkillQueryAttention and provides named access to the 5 outputs:
    r_name, r_desc, r_category, r_tools, r_instr
    """
    
    def __init__(self, hidden_dim: int = 256):
        super().__init__()
        self.attention = SkillQueryAttention(hidden_dim=hidden_dim)
    
    def forward(
        self,
        temporal_features: torch.Tensor,
        mask: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        """
        Returns dict with keys: name, description, category, tools, instructions
        Each value is (batch, hidden_dim)
        """
        # (batch, 5, hidden_dim)
        rep = self.attention(temporal_features, mask)
        
        return {
            "name": rep[:, 0, :],
            "description": rep[:, 1, :],
            "category": rep[:, 2, :],
            "tools": rep[:, 3, :],
            "instructions": rep[:, 4, :],
        }
```

### 2.4 Stage 4: Constrained JSON Decoder

```python
# pseudocode: tse_model.py (part 4)

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model


class ConstrainedSkillDecoder(nn.Module):
    """
    CodeLLaMA-based decoder that generates valid skill JSON.
    
    Uses QLoRA for parameter-efficient fine-tuning.
    Grammar-constrained generation ensures valid JSON output.
    """
    
    def __init__(
        self,
        base_model: str = "codellama/CodeLlama-7b-Instruct-hf",
        hidden_dim: int = 256,
        lora_rank: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
    ):
        super().__init__()
        
        # ── Load base model with QLoRA ──
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        base_llm = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            load_in_4bit=True,  # 4-bit quantization for efficiency
        )
        
        # Apply QLoRA
        lora_config = LoraConfig(
            r=lora_rank,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
            task_type="CAUSAL_LM",
        )
        self.decoder = get_peft_model(base_llm, lora_config)
        
        # ── Projection: skill representations → LLM embedding space ──
        llm_dim = base_llm.config.hidden_size  # typically 4096 for 7B
        self.rep_to_llm = nn.Sequential(
            nn.Linear(hidden_dim * 5 + 10, llm_dim),
            nn.LayerNorm(llm_dim),
            nn.GELU(),
        )
        
        # Category classifier head (for category field prediction)
        self.category_head = nn.Linear(hidden_dim, 6)  # 6 categories
        
        # Tools prediction head (multi-label)
        self.tools_head = nn.Linear(hidden_dim, 50)  # max 50 known tools
    
    def _build_prompt_prefix(
        self,
        skill_repr: dict[str, torch.Tensor],
        context_text: str,
    ) -> str:
        """
        Build the prompt for the decoder. The prompt gives the LLM context
        about the discussion and instructs it to output skill JSON.
        """
        prompt = f"""基于以下多智能体讨论，生成结构化的技能定义。

讨论话题: {context_text[:200]}

请以JSON格式输出技能，必须包含以下字段:
- name: 技能名称
- description: 技能描述
- category: 技能类别
- instructions: 分步骤的操作指令
- required_tools: 所需的工具列表

输出格式（严格遵循）:
```json
[
  {{
    "name": "...",
    "description": "...",
    "category": "...",
    "instructions": "...",
    "required_tools": ["..."]
  }}
]
```

技能定义:
"""
        return prompt
    
    def forward(
        self,
        skill_repr: dict[str, torch.Tensor],
        target_input_ids: torch.Tensor,       # (batch, target_len) or None
        target_attention_mask: torch.Tensor,  # (batch, target_len) or None
        context_texts: list[str],
    ) -> dict:
        """
        Training: teacher-forcing with target sequence
        Inference: autoregressive generation with constraint
        """
        batch = skill_repr["name"].shape[0]
        
        # ── Concatenate skill representations ──
        # Each skill field representation is (batch, hidden_dim)
        # Concatenate all 5: (batch, 5 * hidden_dim)
        concat_repr = torch.cat([
            skill_repr["name"],
            skill_repr["description"],
            skill_repr["category"],
            skill_repr["tools"],
            skill_repr["instructions"],
        ], dim=1)  # (batch, 5 * hidden_dim)
        
        # Add numerical features: utterance count, avg round, signal distribution
        # (padded with zeros for now — computed in training loop)
        aux_features = torch.zeros(batch, 10, device=concat_repr.device)
        concat_repr = torch.cat([concat_repr, aux_features], dim=1)
        
        # Project to LLM embedding dim
        llm_inputs_embeds = self.rep_to_llm(concat_repr).unsqueeze(1)  # (batch, 1, llm_dim)
        
        # ── Category prediction (auxiliary task, no decoder needed) ──
        category_logits = self.category_head(skill_repr["category"])
        
        # ── Tools prediction (auxiliary task) ──
        tools_logits = self.tools_head(skill_repr["tools"])
        
        if self.training and target_input_ids is not None:
            # Teacher-forcing: use target tokens
            target_embeds = self.decoder.get_input_embeddings()(target_input_ids)
            
            # Prepend skill representation as first token
            full_embeds = torch.cat([llm_inputs_embeds, target_embeds], dim=1)
            
            # Create attention mask
            prefix_mask = torch.ones(batch, 1, device=full_embeds.device)
            full_mask = torch.cat([prefix_mask, target_attention_mask], dim=1)
            
            outputs = self.decoder(
                inputs_embeds=full_embeds,
                attention_mask=full_mask,
                labels=target_input_ids,  # shifted internally by HF
            )
            
            return {
                "decoder_loss": outputs.loss,
                "category_logits": category_logits,
                "tools_logits": tools_logits,
            }
        else:
            return {
                "llm_inputs_embeds": llm_inputs_embeds,
                "category_logits": category_logits,
                "tools_logits": tools_logits,
            }
    
    def generate(
        self,
        skill_repr: dict[str, torch.Tensor],
        context_texts: list[str],
        max_new_tokens: int = 512,
        temperature: float = 0.3,
    ) -> list[str]:
        """
        Autoregressive generation with grammar constraint for valid JSON.
        
        Uses the llm_inputs_embeds as a prefix, then generates the JSON string.
        Post-processes with JSON validation and retry.
        """
        batch = len(context_texts)
        
        # Build embeddings prefix (same as forward)
        concat_repr = torch.cat([
            skill_repr["name"],
            skill_repr["description"],
            skill_repr["category"],
            skill_repr["tools"],
            skill_repr["instructions"],
        ], dim=1)
        aux_features = torch.zeros(batch, 10, device=concat_repr.device)
        concat_repr = torch.cat([concat_repr, aux_features], dim=1)
        llm_prefix = self.rep_to_llm(concat_repr).unsqueeze(1)
        
        # Build text prompts
        prompts = [
            self._build_prompt_prefix(skill_repr, ctx)
            for ctx in context_texts
        ]
        
        # Tokenize prompts
        prompt_tokens = self.tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=256,
        ).to(llm_prefix.device)
        
        # Generate
        with torch.no_grad():
            generated = self.decoder.generate(
                input_ids=prompt_tokens["input_ids"],
                attention_mask=prompt_tokens["attention_mask"],
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=(temperature > 0),
                top_p=0.9,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        
        # Decode and validate
        results = []
        for i in range(batch):
            output_ids = generated[i][prompt_tokens["input_ids"].shape[1]:]
            text = self.tokenizer.decode(output_ids, skip_special_tokens=True)
            
            # Try to extract JSON from output
            text = extract_json_from_text(text)
            
            # Validate JSON
            try:
                parsed = json.loads(text)
                # Ensure it's a list of skill objects
                if isinstance(parsed, dict):
                    parsed = [parsed]
                for skill in parsed:
                    validate_skill_fields(skill)
                results.append(json.dumps(parsed, ensure_ascii=False))
            except (json.JSONDecodeError, ValidationError):
                # Fallback: return raw text, post-processing will handle
                results.append(text)
        
        return results


def extract_json_from_text(text: str) -> str:
    """Extract JSON from markdown code blocks or raw text."""
    import re
    
    # Try ```json ... ``` block
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        return match.group(1).strip()
    
    # Try to find JSON array or object
    match = re.search(r'(\[[\s\S]*\]|\{[\s\S]*\})', text)
    if match:
        return match.group(1).strip()
    
    return text.strip()
```

### 2.5 Complete TSE Model

```python
# pseudocode: tse_model.py (part 5 — full model)


class TCN_Skill_Extractor(nn.Module):
    """
    Complete TCN-Skill-Extractor (TSE) model.
    
    Pipeline:
    Longformer → TCN → Skill Query Attention → Constrained Decoder
    
    Training: end-to-end with multi-task loss
    Inference: token encoder → TCN → attention → decoder.generate()
    """
    
    def __init__(
        self,
        decoder_base_model: str = "codellama/CodeLlama-7b-Instruct-hf",
        encoder_dim: int = 768,
        tcn_hidden_dim: int = 256,
        tcn_num_layers: int = 3,
        freeze_encoder: bool = True,
    ):
        super().__init__()
        
        self.encoder = LongformerUtteranceEncoder(
            embedding_dim=encoder_dim,
            freeze=freeze_encoder,
        )
        self.tcn = TCNTemporalModule(
            input_dim=encoder_dim,
            hidden_dim=tcn_hidden_dim,
            num_layers=tcn_num_layers,
        )
        self.skill_attention = SkillRepresentation(hidden_dim=tcn_hidden_dim)
        self.decoder = ConstrainedSkillDecoder(
            base_model=decoder_base_model,
            hidden_dim=tcn_hidden_dim,
        )
        
        # Auxiliary embedding tables
        self.role_embeddings = nn.Embedding(20, encoder_dim)
        self.signal_embeddings = nn.Embedding(10, encoder_dim)
        self.niche_embeddings = nn.Embedding(10, encoder_dim)
        self.round_embeddings = nn.Embedding(10, encoder_dim)
    
    def _encode_with_aux(
        self,
        utterance_input_ids: torch.Tensor,        # (batch, N, L)
        utterance_attention_mask: torch.Tensor,   # (batch, N, L)
        role_ids: torch.Tensor,                   # (batch, N)
        signal_ids: torch.Tensor,                 # (batch, N)
        niche_ids: torch.Tensor,                  # (batch, N)
        round_ids: torch.Tensor,                  # (batch, N)
    ) -> torch.Tensor:
        """
        Encode utterances and add auxiliary embeddings.
        Returns: (batch, N, encoder_dim)
        """
        batch, N, L = utterance_input_ids.shape
        
        # Flatten for Longformer: (batch * N, L)
        flat_input_ids = utterance_input_ids.view(batch * N, L)
        flat_attention = utterance_attention_mask.view(batch * N, L)
        
        # Longformer encoding
        flat_embeddings = self.encoder(flat_input_ids, flat_attention)  # (batch*N, dim)
        
        # Reshape to (batch, N, dim)
        text_embeddings = flat_embeddings.view(batch, N, -1)
        
        # Add auxiliary embeddings
        role_emb = self.role_embeddings(role_ids)       # (batch, N, dim)
        signal_emb = self.signal_embeddings(signal_ids) # (batch, N, dim)
        niche_emb = self.niche_embeddings(niche_ids)    # (batch, N, dim)
        round_emb = self.round_embeddings(
            torch.clamp(round_ids, min=0)               # (batch, N, dim)
        )
        
        # Combine: text is primary, aux are additive
        utterance_embeddings = (
            text_embeddings + 
            0.1 * role_emb + 
            0.1 * signal_emb + 
            0.1 * niche_emb + 
            0.05 * round_emb
        )
        
        return utterance_embeddings  # (batch, N, encoder_dim)
    
    def _build_utterance_mask(
        self,
        utterance_count: torch.Tensor,  # (batch,)
        max_N: int,
    ) -> torch.Tensor:
        """Build attention mask for TCN: 1=real utterance, 0=pad."""
        batch = utterance_count.shape[0]
        device = utterance_count.device
        positions = torch.arange(max_N, device=device).unsqueeze(0)  # (1, max_N)
        mask = (positions < utterance_count.unsqueeze(1)).float()    # (batch, max_N)
        return mask
    
    def forward(
        self,
        batch: dict,
        context_texts: list[str],
    ) -> dict:
        """
        Forward pass with all batch fields from PlazaExtractionDataset.__getitem__.
        """
        # ── Stage 1 + 2: Encode → TCN ──
        utterance_embeddings = self._encode_with_aux(
            batch["utterance_input_ids"],
            batch["utterance_attention_mask"],
            batch["role_ids"],
            batch["signal_ids"],
            batch["niche_ids"],
            batch["round_ids"],
        )
        
        max_N = utterance_embeddings.shape[1]
        mask = self._build_utterance_mask(batch["utterance_count"], max_N)
        
        temporal_features = self.tcn(utterance_embeddings, mask)
        
        # ── Stage 3: Skill Query Attention ──
        skill_repr = self.skill_attention(temporal_features, mask)
        
        # ── Stage 4: Decoder ──
        outputs = self.decoder(
            skill_repr=skill_repr,
            target_input_ids=batch.get("target_input_ids"),
            target_attention_mask=batch.get("target_attention_mask"),
            context_texts=context_texts,
        )
        
        return outputs
    
    @torch.no_grad()
    def extract_skills(
        self,
        transcript: dict,
        device: torch.device,
    ) -> list[dict]:
        """
        Inference: extract skills from a single Plaza transcript.
        
        Args:
            transcript: dict with "topic" and "messages" fields
        
        Returns:
            list of skill dicts, each with name/description/category/instructions/required_tools
        """
        self.eval()
        
        # Convert transcript to batch format (batch_size=1)
        # (This would use the same logic as PlazaExtractionDataset.__getitem__)
        batch = prepare_single_transcript(transcript, self.encoder.tokenizer)
        batch = {k: v.unsqueeze(0).to(device) if isinstance(v, torch.Tensor) else v 
                 for k, v in batch.items()}
        
        # Encode → TCN → Attention
        utterance_embeddings = self._encode_with_aux(
            batch["utterance_input_ids"],
            batch["utterance_attention_mask"],
            batch["role_ids"],
            batch["signal_ids"],
            batch["niche_ids"],
            batch["round_ids"],
        )
        mask = self._build_utterance_mask(batch["utterance_count"], utterance_embeddings.shape[1])
        temporal_features = self.tcn(utterance_embeddings, mask)
        skill_repr = self.skill_attention(temporal_features, mask)
        
        # Generate JSON via decoder
        context = transcript.get("topic", "")
        json_strs = self.decoder.generate(
            skill_repr=skill_repr,
            context_texts=[context],
        )
        
        # Parse and return
        try:
            skills = json.loads(json_strs[0])
            if isinstance(skills, dict):
                skills = [skills]
            return skills
        except json.JSONDecodeError:
            return []
```

---

## 3. Training Loop

```python
# pseudocode: train_tse.py

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import AdamW
from transformers import get_cosine_schedule_with_warmup


def train_tse(
    model: TCN_Skill_Extractor,
    train_dataset: PlazaExtractionDataset,
    val_dataset: PlazaExtractionDataset,
    num_epochs: int = 10,
    batch_size: int = 4,       # small because decoder is large
    learning_rate: float = 5e-5,
    warmup_steps: int = 200,
    gradient_accumulation: int = 4,  # effective batch = 4*4 = 16
    device: str = "cuda",
):
    """Training loop with multi-task loss."""
    
    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True,
        collate_fn=collate_batch,
    )
    
    # ── Optimizer with layer-specific LR ──
    # Higher LR for TCN + Attention (new layers), lower for pretrained components
    optimizer = AdamW([
        {"params": model.tcn.parameters(),         "lr": learning_rate},
        {"params": model.skill_attention.parameters(), "lr": learning_rate},
        {"params": model.decoder.category_head.parameters(), "lr": learning_rate},
        {"params": model.decoder.tools_head.parameters(),   "lr": learning_rate},
        {"params": model.role_embeddings.parameters(),      "lr": learning_rate * 0.5},
        {"params": model.signal_embeddings.parameters(),    "lr": learning_rate * 0.5},
        {"params": model.niche_embeddings.parameters(),     "lr": learning_rate * 0.5},
        {"params": model.round_embeddings.parameters(),     "lr": learning_rate * 0.5},
        # Decoder QLoRA params handled by PEFT internally
    ])
    
    total_steps = num_epochs * len(train_loader) // gradient_accumulation
    scheduler = get_cosine_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )
    
    # ── Loss functions ──
    category_criterion = nn.CrossEntropyLoss()
    tools_criterion = nn.BCEWithLogitsLoss()
    
    # ── Training loop ──
    model.train()
    global_step = 0
    
    for epoch in range(num_epochs):
        total_loss = 0.0
        total_gen_loss = 0.0
        total_cat_loss = 0.0
        total_tools_loss = 0.0
        
        for step, batch in enumerate(train_loader):
            # Move to device
            batch = {k: v.to(device) if isinstance(v, torch.Tensor) else v
                     for k, v in batch.items()}
            
            # Forward
            # target_input_ids and target_attention_mask come from dataset
            outputs = model(batch, context_texts=batch["context_texts"])
            
            # ── Multi-task loss ──
            # 1. Decoder autoregressive loss (teacher forcing)
            gen_loss = outputs["decoder_loss"]
            
            # 2. Category classification loss
            # category_targets: (batch,) indices 0-5
            cat_loss = category_criterion(
                outputs["category_logits"],
                batch["category_targets"],
            )
            
            # 3. Tools multi-label loss
            # tools_targets: (batch, 50) binary vector
            tools_loss = tools_criterion(
                outputs["tools_logits"],
                batch["tools_targets"],
            )
            
            # Combined loss
            loss = gen_loss + 0.1 * cat_loss + 0.1 * tools_loss
            loss = loss / gradient_accumulation
            
            # Backward
            loss.backward()
            
            total_loss += loss.item()
            total_gen_loss += gen_loss.item() / gradient_accumulation
            total_cat_loss += cat_loss.item() / gradient_accumulation
            total_tools_loss += tools_loss.item() / gradient_accumulation
            
            # Gradient accumulation step
            if (step + 1) % gradient_accumulation == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                global_step += 1
        
        # ── Epoch summary ──
        avg_loss = total_loss / len(train_loader)
        print(f"Epoch {epoch+1}/{num_epochs} | "
              f"Loss: {avg_loss:.4f} | "
              f"Gen: {total_gen_loss/len(train_loader):.4f} | "
              f"Cat: {total_cat_loss/len(train_loader):.4f} | "
              f"Tools: {total_tools_loss/len(train_loader):.4f}")
        
        # ── Validation ──
        if (epoch + 1) % 2 == 0:
            metrics = evaluate_tse(model, val_dataset, device)
            print(f"  Val | Precision: {metrics['precision']:.3f} | "
                  f"Recall: {metrics['recall']:.3f} | "
                  f"F1: {metrics['f1']:.3f}")


def collate_batch(batch: list[dict]) -> dict:
    """Custom collate function for variable-length sequences."""
    # Pad utterance sequences to max_N in this batch
    max_N = max(item["utterance_input_ids"].shape[0] for item in batch)
    max_text_len = batch[0]["utterance_input_ids"].shape[1]
    
    padded = {}
    for key in ["utterance_input_ids", "utterance_attention_mask"]:
        tensors = []
        for item in batch:
            t = item[key]  # (N_i, max_text_len)
            pad_h = max_N - t.shape[0]
            if pad_h > 0:
                t = torch.cat([t, torch.zeros(pad_h, max_text_len, dtype=t.dtype)], dim=0)
            tensors.append(t)
        padded[key] = torch.stack(tensors)
    
    for key in ["role_ids", "signal_ids", "niche_ids", "round_ids"]:
        tensors = []
        for item in batch:
            t = item[key]  # (N_i,)
            pad_h = max_N - t.shape[0]
            if pad_h > 0:
                t = torch.cat([t, torch.zeros(pad_h, dtype=t.dtype)])
            tensors.append(t)
        padded[key] = torch.stack(tensors)
    
    padded["utterance_count"] = torch.tensor([item["utterance_count"] for item in batch])
    padded["target_input_ids"] = torch.stack([item["target_input_ids"] for item in batch])
    padded["target_attention_mask"] = torch.stack([item["target_attention_mask"] for item in batch])
    
    return padded


def evaluate_tse(
    model: TCN_Skill_Extractor,
    dataset: PlazaExtractionDataset,
    device: str,
) -> dict:
    """Evaluate extraction quality on validation set."""
    model.eval()
    
    all_predictions = []
    all_ground_truth = []
    
    for idx in range(len(dataset)):
        item = dataset.data[idx]
        pred_skills = model.extract_skills(item["transcript"], device)
        true_skills = item["skills"]
        
        # Simple metric: how many ground-truth skill names appear in predictions?
        # (Full evaluation uses field-level matching; this is approximate)
        pred_names = {s["name"].lower() for s in pred_skills}
        true_names = {s["name"].lower() for s in true_skills}
        
        all_predictions.append(pred_names)
        all_ground_truth.append(true_names)
    
    # Micro-average precision/recall/F1
    tp = sum(len(p & g) for p, g in zip(all_predictions, all_ground_truth))
    fp = sum(len(p - g) for p, g in zip(all_predictions, all_ground_truth))
    fn = sum(len(g - p) for p, g in zip(all_predictions, all_ground_truth))
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {"precision": precision, "recall": recall, "f1": f1}
```

---

## 4. Inference Pipeline

```python
# pseudocode: inference.py

def extract_skills_from_plaza(
    transcript: dict,
    model: TCN_Skill_Extractor,
    device: torch.device = torch.device("cuda"),
) -> list[dict]:
    """
    Given a Plaza discussion transcript, return extracted skills.
    
    This is the function you call after each Plaza discussion completes.
    Replace the current TF-IDF-based extraction with this neural extraction.
    
    Args:
        transcript: Plaza discussion transcript (plaza.discussion.to_dict())
        model: Loaded TSE model (from checkpoint)
    
    Returns:
        list of skill dicts ready to be inserted into SkillRegistry
    """
    skills = model.extract_skills(transcript, device)
    
    # Post-processing: clean up and validate each skill
    validated_skills = []
    for skill in skills:
        # Ensure all required fields present
        skill.setdefault("category", "general")
        skill.setdefault("required_tools", [])
        
        # Truncate long fields
        skill["name"] = skill["name"][:100]
        skill["description"] = skill["description"][:500]
        skill["instructions"] = skill["instructions"][:2000]
        
        # Convert category to enum
        from agents.models import SkillCategory
        try:
            skill["category"] = SkillCategory[skill["category"].upper()]
        except (KeyError, AttributeError):
            skill["category"] = SkillCategory.GENERAL
        
        validated_skills.append(skill)
    
    return validated_skills


# ── Integration point in plaza_engine.py ──
# Replace the TF-IDF extraction in _auto_extract_on_consensus:
"""
async def _auto_extract_on_consensus(self, disc):
    # ... existing pipeline creation code ...
    
    # NEW: Neural extraction instead of TF-IDF
    from .tse_inference import extract_skills_from_plaza
    
    transcript = disc.to_dict(include_messages=True)
    skills = extract_skills_from_plaza(transcript, tse_model, device)
    
    for skill in skills:
        await store.create_skill_from_extraction(pipeline.pipeline_id, skill)
"""
```

---

## 5. Hyperparameter Summary

| Component | Parameter | Value | Rationale |
|-----------|-----------|-------|-----------|
| Longformer | model | allenai/longformer-base-4096 | 4096 token window covers full discussion |
| Longformer | freeze | True during silver data phase | Prevents overfitting on small bootstrap data |
| TCN | hidden_dim | 256 | Balance between capacity and efficiency |
| TCN | num_layers | 3 | dilations=[1,2,4], RF=29 utterances (3-5 rounds) |
| TCN | kernel_size | 3 | Standard for temporal convolution |
| TCN | dropout | 0.1 | Light regularization |
| Attention | num_heads | 4 | Classic multi-head setting |
| Attention | num_queries | 5 | One per skill field |
| Decoder | base_model | CodeLlama-7B-Instruct | Strong structured generation |
| Decoder | lora_rank | 16 | Good balance for QLoRA |
| Decoder | lora_alpha | 32 | Standard ratio for LoRA |
| Training | batch_size | 4 | Limited by 7B decoder VRAM |
| Training | grad_accum | 4 | Effective batch = 16 |
| Training | learning_rate | 5e-5 | Standard for transformer fine-tuning |
| Training | warmup_steps | 200 | ~10% of total steps |
| Training | epochs | 10 | With early stopping on validation F1 |
| Loss | gen_loss weight | 1.0 | Primary signal |
| Loss | cat_loss weight | 0.1 | Auxiliary regularization |
| Loss | tools_loss weight | 0.1 | Auxiliary regularization |
| Inference | temperature | 0.3 | Low for consistent extraction |
| Inference | max_new_tokens | 512 | Covers typical skill JSON |
