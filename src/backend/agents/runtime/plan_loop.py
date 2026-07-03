"""Shared plan-based loop runtime used by ChatHarness agent_loop APIs."""

from __future__ import annotations

import time
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple

from ..execution_registry import ToolPermissionContext
from .events import make_runtime_event_emitter


def _extract_available_tool_names(tools: Optional[List[Dict[str, Any]]]) -> List[str]:
    names: List[str] = []
    for tool in tools or []:
        name = ((tool.get("function") or {}).get("name") or "").strip()
        if name:
            names.append(name)
    return names


def _build_synthesis_prompt(
    prompt: str,
    plan: Any,
    observations: List[Dict[str, Any]],
) -> str:
    obs_text = "\n".join(
        f"[{o['tool']}] {'✅' if o['success'] else '❌'}: {o['output'][:300]}"
        for o in observations
    )
    return (
        f"用户问题: {prompt}\n\n"
        f"执行计划已完成 ({plan.completed_steps}/{len(plan.steps)} 步成功).\n\n"
        f"工具调用结果:\n{obs_text}\n\n"
        f"请根据以上结果，用中文(技术术语英文保留)给用户一个完整、专业的回答。"
    )


def _deps_satisfied(plan: Any, step: Any, completed_status: Any) -> bool:
    return all(
        plan.steps[dep - 1].status == completed_status
        for dep in step.depends_on
        if dep <= len(plan.steps)
    )


def _build_plan(
    *,
    prompt: str,
    plan_builder: Callable[..., Any],
    tools: Optional[List[Dict[str, Any]]],
    plan_middleware: Optional[Callable[[Any], Any]],
) -> Any:
    plan = plan_builder(
        prompt,
        available_tools=_extract_available_tool_names(tools),
    )
    if plan_middleware:
        plan = plan_middleware(plan)
    plan.status = "running"
    return plan


def _mark_step_skipped(step: Any, reason: str, skipped_status: Any) -> None:
    step.status = skipped_status
    step.error = reason


def _complete_non_tool_step(step: Any, completed_status: Any) -> None:
    step.status = completed_status
    if step.action == "think":
        step.result = f"思考: {step.description}"
    elif step.action == "delegate":
        step.result = f"已委派: {step.description}"


async def _execute_tool_step(
    *,
    executor: Any,
    step: Any,
    agent_id: str,
    permission_context: Optional[ToolPermissionContext],
    completed_status: Any,
    failed_status: Any,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    started_at = time.monotonic()
    result = await executor.execute(
        step.tool_name,
        step.tool_args,
        agent_id=agent_id,
        permission_context=permission_context,
    )
    step.duration_ms = (time.monotonic() - started_at) * 1000
    step.status = completed_status if result.success else failed_status
    step.result = result.output
    if not result.success:
        step.error = result.error

    observation = {
        "step": step.step_id,
        "tool": step.tool_name,
        "success": result.success,
        "output": result.output[:1000],
    }
    event_payload = {
        "step_id": step.step_id,
        "tool": step.tool_name,
        "success": result.success,
        "output": result.output[:500],
        "duration_ms": step.duration_ms,
    }
    return observation, event_payload


async def run_plan_loop(
    harness: Any,
    *,
    prompt: str,
    plan_builder: Callable[..., Any],
    agent_id: str = "",
    team_id: str = "",
    session_id: str = "",
    system_prompt: str = "",
    tools: Optional[List[Dict[str, Any]]] = None,
    max_iterations: int = 10,
    plan_middleware: Optional[Callable[[Any], Any]] = None,
    permission_context: Optional[ToolPermissionContext] = None,
    on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
) -> Any:
    from ..chat_harness import AgentLoopResult, PlanStepStatus
    from ..tool_executor import get_tool_executor

    executor = get_tool_executor()
    plan = _build_plan(
        prompt=prompt,
        plan_builder=plan_builder,
        tools=tools,
        plan_middleware=plan_middleware,
    )
    _runtime_id, emit_event = make_runtime_event_emitter(
        loop_kind="plan_loop",
        session_id=session_id,
        on_event=on_event,
    )

    observations: List[Dict[str, Any]] = []
    iteration = 0
    emit_event("plan_start", {"goal": prompt, "steps": len(plan.steps)})

    for step in plan.steps:
        if iteration >= max_iterations:
            _mark_step_skipped(step, "Iteration cap reached", PlanStepStatus.SKIPPED)
            emit_event("step_complete", {"step": step.to_dict()})
            continue
        iteration += 1
        emit_event("step_start", {"step": step.to_dict()})

        if step.action == "tool_call" and step.tool_name:
            if not _deps_satisfied(plan, step, PlanStepStatus.COMPLETED):
                _mark_step_skipped(step, "Dependencies not met", PlanStepStatus.SKIPPED)
                emit_event("step_complete", {"step": step.to_dict()})
                continue

            step.status = PlanStepStatus.RUNNING
            observation, tool_event = await _execute_tool_step(
                executor=executor,
                step=step,
                agent_id=agent_id,
                permission_context=permission_context,
                completed_status=PlanStepStatus.COMPLETED,
                failed_status=PlanStepStatus.FAILED,
            )
            observations.append(observation)
            emit_event("tool_result", tool_event)
            emit_event("step_complete", {"step": step.to_dict()})
            continue

        _complete_non_tool_step(step, PlanStepStatus.COMPLETED)
        emit_event("step_complete", {"step": step.to_dict()})

    synthesis_prompt = _build_synthesis_prompt(prompt, plan, observations)
    final_result = await harness.chat(
        synthesis_prompt,
        agent_id=agent_id,
        team_id=team_id,
        session_id=session_id,
        system_prompt=system_prompt,
        model_override="",
    )
    plan.status = "completed"
    plan.final_response = final_result.response
    emit_event("plan_complete", {"iterations": iteration, "observations": len(observations)})
    emit_event("loop_end", {"reason": "completed", "iterations": iteration})
    return AgentLoopResult(
        plan=plan,
        observations=observations,
        final_response=final_result.response,
        turn_result=final_result,
        iterations=iteration,
    )


async def stream_plan_loop(
    harness: Any,
    *,
    prompt: str,
    plan_builder: Callable[..., Any],
    agent_id: str = "",
    team_id: str = "",
    session_id: str = "",
    system_prompt: str = "",
    tools: Optional[List[Dict[str, Any]]] = None,
    max_iterations: int = 10,
    plan_middleware: Optional[Callable[[Any], Any]] = None,
    permission_context: Optional[ToolPermissionContext] = None,
    on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
) -> AsyncIterator[Dict[str, Any]]:
    from ..chat_harness import PlanStepStatus
    from ..tool_executor import get_tool_executor

    executor = get_tool_executor()
    plan = _build_plan(
        prompt=prompt,
        plan_builder=plan_builder,
        tools=tools,
        plan_middleware=plan_middleware,
    )
    _runtime_id, emit_event = make_runtime_event_emitter(
        loop_kind="plan_loop",
        session_id=session_id,
        on_event=on_event,
    )
    observations: List[Dict[str, Any]] = []
    iteration = 0

    yield emit_event("plan_start", {"goal": prompt, "steps": len(plan.steps), "plan": plan.to_dict()})

    for step in plan.steps:
        if iteration >= max_iterations:
            _mark_step_skipped(step, "Iteration cap reached", PlanStepStatus.SKIPPED)
            yield emit_event("step_complete", {"step": step.to_dict()})
            continue
        iteration += 1

        yield emit_event("step_start", {"step": step.to_dict()})

        if step.action == "tool_call" and step.tool_name:
            if not _deps_satisfied(plan, step, PlanStepStatus.COMPLETED):
                _mark_step_skipped(step, "Dependencies not met", PlanStepStatus.SKIPPED)
                yield emit_event("step_complete", {"step": step.to_dict()})
                continue

            step.status = PlanStepStatus.RUNNING
            observation, tool_event = await _execute_tool_step(
                executor=executor,
                step=step,
                agent_id=agent_id,
                permission_context=permission_context,
                completed_status=PlanStepStatus.COMPLETED,
                failed_status=PlanStepStatus.FAILED,
            )
            observations.append(observation)
            yield emit_event("tool_result", tool_event)
            yield emit_event("step_complete", {"step": step.to_dict()})
            continue

        _complete_non_tool_step(step, PlanStepStatus.COMPLETED)
        yield emit_event("step_complete", {"step": step.to_dict()})

    plan.status = "completed"
    yield emit_event(
        "plan_complete",
        {
            "progress": plan.progress,
            "iterations": iteration,
            "observations": len(observations),
        },
    )

    synthesis_prompt = _build_synthesis_prompt(prompt, plan, observations)
    async for chunk in harness.stream_chat(
        synthesis_prompt,
        agent_id=agent_id,
        team_id=team_id,
        session_id=session_id,
        system_prompt=system_prompt,
    ):
        yield chunk
    emit_event("loop_end", {"reason": "completed", "iterations": iteration})
