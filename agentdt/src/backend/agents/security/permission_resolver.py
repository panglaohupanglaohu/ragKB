from __future__ import annotations

from typing import Dict, Iterable, Set

from ..execution_registry import ToolPermissionContext
from ..models import AccessLevel, AgentProfile
from ..tool_registry import ToolRegistry


READ_ONLY_TOOLSETS: Dict[str, Set[str]] = {
    "code": {"read_file", "search_files", "list_directory"},
    "docs": {"read_file", "search_files", "list_directory"},
    "tests": {"read_file", "search_files", "list_directory"},
    "web": {"web_search", "navigate_url", "extract_content", "web_extract", "screenshot"},
    "tasks": {"list_agents", "list_capabilities", "delegate_task"},
    "agents": {"list_agents", "list_capabilities", "send_message", "broadcast"},
    "tools": {"list_capabilities", "skill_list", "skill_view"},
    "architecture": {"read_file", "search_files", "list_directory", "web_search"},
    "operations": {"read_file", "search_files", "list_directory", "session_search", "memory_read"},
    "security": {"read_file", "search_files", "list_directory", "session_search", "memory_read"},
    "incidents": {"read_file", "search_files", "list_directory", "session_search", "memory_read", "send_message", "broadcast"},
    "infra": {"read_file", "search_files", "list_directory", "session_search", "memory_read"},
    "billing": {"read_file", "search_files", "list_directory"},
    "aws": {"read_file", "search_files", "list_directory"},
    "azure": {"read_file", "search_files", "list_directory"},
    "aliyun": {"read_file", "search_files", "list_directory"},
    "gcp": {"read_file", "search_files", "list_directory"},
    "domestic_cloud": {"read_file", "search_files", "list_directory"},
    "datacenter_energy": {"read_file", "search_files", "list_directory"},
    "sensors": {"read_file", "search_files", "list_directory"},
    "plc": {"read_file", "search_files", "list_directory"},
    "policies": {"read_file", "search_files", "list_directory"},
    "heritage": {"read_file", "search_files", "list_directory"},
    "alerts": {"read_file", "search_files", "list_directory", "send_message", "broadcast"},
}

WRITE_TOOLSETS: Dict[str, Set[str]] = {
    "code": {"write_file", "edit_file", "run_python"},
    "docs": {"write_file", "edit_file"},
    "tests": {"run_shell", "run_python"},
    "tasks": {"schedule_task", "delegate_task"},
    "agents": {"send_message", "broadcast", "delegate_task", "mixture_of_agents"},
    "tools": {"skill_manage"},
    "architecture": {"write_file", "edit_file", "run_python"},
    "operations": {"run_shell", "run_python", "publish_event", "schedule_task"},
    "security": {"run_shell", "run_python", "publish_event"},
    "incidents": {"run_shell", "run_python", "publish_event", "schedule_task"},
    "infra": {"run_shell", "run_python", "write_file", "edit_file"},
    "aws": {"run_shell", "run_python"},
    "azure": {"run_shell", "run_python"},
    "aliyun": {"run_shell", "run_python"},
    "gcp": {"run_shell", "run_python"},
    "domestic_cloud": {"run_shell", "run_python"},
    "datacenter_energy": {"run_python", "publish_event"},
    "sensors": {"run_python", "publish_event"},
    "plc": {"run_python", "publish_event"},
    "policies": {"write_file", "edit_file"},
    "heritage": {"write_file", "edit_file"},
    "alerts": {"publish_event", "schedule_task"},
}

ADMIN_TOOLSETS: Dict[str, Set[str]] = {
    "code": {"delete_file"},
    "docs": {"delete_file"},
    "tests": {"delete_file"},
    "tasks": {"cron_trigger", "set_alarm", "watch_file"},
    "agents": {"subscribe_channel", "publish_event"},
    "operations": {"delete_file"},
    "security": {"delete_file"},
    "incidents": {"set_alarm"},
    "infra": {"delete_file"},
}


class PermissionResolver:
    """Turn Agent permissions into a deny-list ToolPermissionContext."""

    def __init__(self) -> None:
        registry = ToolRegistry()
        registry.load_defaults()
        self._all_tools = {tool.name for tool in registry.list_enabled()}

    def build_context(self, agent: AgentProfile) -> ToolPermissionContext:
        if not agent.permissions:
            return ToolPermissionContext()

        allowed = set()
        for perm in agent.permissions:
            resource = (perm.resource or "").strip().lower()
            allowed.update(self._allowed_for_resource(resource, perm.access_level))
            allowed.update(tool_name for tool_name in perm.allowed_tools if tool_name)

        if not allowed:
            return ToolPermissionContext.from_lists(deny_names=sorted(self._all_tools))

        deny_names = sorted(self._all_tools - allowed)
        return ToolPermissionContext.from_lists(deny_names=deny_names)

    def _allowed_for_resource(self, resource: str, access_level: AccessLevel) -> Set[str]:
        allowed = set(READ_ONLY_TOOLSETS.get(resource, set()))
        if access_level in {AccessLevel.WRITE, AccessLevel.ADMIN}:
            allowed.update(WRITE_TOOLSETS.get(resource, set()))
        if access_level == AccessLevel.ADMIN:
            allowed.update(ADMIN_TOOLSETS.get(resource, set()))
        return allowed & self._all_tools


def filter_tool_names(tool_names: Iterable[str], permission_context: ToolPermissionContext) -> Set[str]:
    return {tool_name for tool_name in tool_names if not permission_context.blocks(tool_name)}
