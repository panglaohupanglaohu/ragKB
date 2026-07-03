# -*- coding: utf-8 -*-
"""SECS — Self-Evolving Collaborative Sandbox (自进化协同沙箱系统).

四维一体架构:
1. 环境语义映射层 (MADTwin) — world_state.py
2. 认知进化循环层 (AAS Zero-Exp) — zero_exp_engine.py + memory_system.py
3. 策略试错实验层 (TwinLoop) — twin_loop.py + drift_detector.py
4. 集体智慧对齐层 (DT-MADDPG) — global_critic.py + strategy_aligner.py
"""
