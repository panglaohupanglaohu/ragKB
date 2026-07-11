# -*- coding: utf-8 -*-
"""AgentsGroup2026 Agent Team Framework — Skill Registry.

Provides default skill definitions across general, digital-twin, and automation
categories, plus a registry class for runtime skill management.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import SkillCategory, SkillDefinition


def get_default_skills() -> List[SkillDefinition]:
    """Return the default catalog of skill definitions."""

    SC = SkillCategory
    SD = SkillDefinition
    return [
        # ── General skills ─────────────────────────────────────────────
        SD(
            name="competitive_analysis",
            description="Analyze competitors and market positioning",
            category=SC.GENERAL,
            required_tools=['web_search', 'extract_content'],
            instructions="## 竞品分析\n\n1. 使用 web_search 搜索竞品信息\n2. 提取关键数据：市场份额、产品特性、定价策略\n3. 生成 SWOT 对比矩阵\n4. 输出结构化分析报告"),
        SD(
            name="complex_task_executor",
            description="Break down and execute complex multi-step tasks",
            category=SC.GENERAL,
            required=True,
            required_tools=['run_python', 'run_shell', 'send_message'],
            instructions="## 复杂任务执行\n\n1. 将任务分解为可执行子步骤\n2. 评估每步所需工具和依赖\n3. 按序执行，遇错时回退重试\n4. 汇总结果并报告进度"),
        SD(
            name="content_research_writer",
            description="Research topics and produce written content",
            category=SC.GENERAL,
            required_tools=['web_search', 'extract_content', 'write_file'],
            instructions="## 内容研究与写作\n\n1. 确认主题和目标受众\n2. 使用 web_search 收集资料\n3. 提取关键信息并整理大纲\n4. 撰写结构化内容\n5. 保存到工作区文件"),
        SD(
            name="content_writing",
            description="Write and edit documentation and reports",
            category=SC.GENERAL,
            required_tools=['write_file', 'read_file'],
            instructions="## 文档写作\n\n1. 读取现有文档了解上下文\n2. 根据需求撰写/修改内容\n3. 确保格式规范、语言专业\n4. 保存并通知相关人员"),
        SD(
            name="data_analysis",
            description="Analyze datasets and produce insights",
            category=SC.GENERAL,
            required_tools=['run_python', 'read_file'],
            instructions="## 数据分析\n\n1. 读取数据文件\n2. 使用 Python 进行统计分析\n3. 生成可视化图表\n4. 总结关键发现和趋势\n5. 给出数据驱动的建议"),
        SD(
            name="mcp_installer",
            description="Install and configure MCP server integrations",
            category=SC.GENERAL,
            required=True,
            required_tools=['run_shell', 'write_file', 'read_file'],
            instructions="## MCP 服务器安装\n\n1. 检查目标 MCP 服务器兼容性\n2. 执行安装命令\n3. 配置连接参数\n4. 验证连接状态\n5. 注册到工具目录"),
        SD(
            name="meeting_notes",
            description="Capture and summarize meeting notes",
            category=SC.GENERAL,
            required_tools=['write_file'],
            instructions="## 会议记录\n\n1. 记录参会人员和议题\n2. 按时间线记录讨论要点\n3. 标记决策事项和待办\n4. 生成结构化会议纪要\n5. 分发给相关人员"),
        SD(
            name="skill_creator",
            description="Create new custom skills from descriptions",
            category=SC.GENERAL,
            required=True,
            required_tools=['write_file', 'read_file'],
            instructions="## 技能创建\n\n1. 分析技能需求描述\n2. 确定所需工具和流程\n3. 编写技能指令模板\n4. 创建技能定义文件\n5. 注册到技能目录"),
        SD(
            name="web_research",
            description="Conduct web research and summarize findings",
            category=SC.GENERAL,
            required_tools=['web_search', 'navigate_url', 'extract_content'],
            instructions="## 网络研究\n\n1. 制定搜索策略和关键词\n2. 多轮搜索收集信息\n3. 访问并提取相关页面内容\n4. 交叉验证信息准确性\n5. 生成研究报告"),
        # ── Digital Twin skills ────────────────────────────────────────
        SD(name="dt_camera_control", description="Control digital twin camera views and animations",
            category=SC.DIGITAL_TWIN, required_tools=['dt_camera_move'],
            instructions="## 数字孪生相机控制\n\n使用 dt_camera_move 控制相机位置、目标点和过渡动画。支持预设视角（top/front/side/iso）和自定义坐标。"),
        SD(name="dt_coordinate_system", description="Manage coordinate system transformations",
            category=SC.DIGITAL_TWIN, required_tools=['dt_model_transform'],
            instructions="## 坐标系管理\n\n1. 理解场景坐标系（Y-up，单位:米）\n2. 使用 dt_model_transform 进行平移/旋转/缩放\n3. 处理世界坐标与局部坐标转换"),
        SD(name="dt_model_layout", description="Arrange and layout 3D models in the scene",
            category=SC.DIGITAL_TWIN, required_tools=['dt_model_load', 'dt_model_transform'],
            instructions="## 3D模型布局\n\n1. 加载模型到场景\n2. 调整位置/旋转/缩放\n3. 确保各模型间距和对齐\n4. 设置碰撞体积"),
        SD(name="dt_model_import", description="Import 3D models from various formats",
            category=SC.DIGITAL_TWIN, required_tools=['dt_model_load'],
            instructions="## 模型导入\n\n支持格式: GLB/GLTF/OBJ/FBX。加载模型并设置初始变换。"),
        SD(name="dt_interaction_actions", description="Define interactive inspection paths and actions",
            category=SC.DIGITAL_TWIN, required_tools=['dt_inspection_path', 'dt_camera_move'],
            instructions="## 交互巡检\n\n1. 定义巡检路径航路点\n2. 设置相机飞行速度和模式\n3. 在关键点添加标注和检查项"),
        SD(name="dt_material_change", description="Change materials and textures on models",
            category=SC.DIGITAL_TWIN, required_tools=['dt_material_set'],
            instructions="## 材质修改\n\n使用 dt_material_set 修改颜色/金属度/粗糙度。支持PBR材质参数。"),
        SD(name="dt_physics_simulation", description="Configure and run physics simulations",
            category=SC.DIGITAL_TWIN, required_tools=['dt_physics_toggle'],
            instructions="## 物理模拟\n\n控制重力、碰撞检测和刚体动力学。用于物理模拟和系统分析。"),
        SD(name="dt_lighting_control", description="Control scene lighting and shadows",
            category=SC.DIGITAL_TWIN, required_tools=['dt_light_adjust'],
            instructions="## 灯光控制\n\n调整环境光/方向光/点光源的强度、颜色和位置。支持昼夜模拟。"),
        SD(name="dt_rendering_control", description="Control rendering pipeline and effects",
            category=SC.DIGITAL_TWIN, required_tools=['dt_render_mode'],
            instructions="## 渲染控制\n\n切换实体/线框/X光/热力图模式。用于不同分析场景。"),

        # ── Automation skills ──────────────────────────────────────────
        SD(name="auto_report", description="定时生成工作报告",
            category=SC.AUTOMATION, icon="📊", required_tools=['write_file'],
            instructions="## 自动报告\n\n1. 收集系统运行数据\n2. 统计关键指标\n3. 生成结构化报告\n4. 按时发送给相关人员"),
        SD(name="auto_monitor", description="监控系统状态并报警",
            category=SC.AUTOMATION, icon="🔔", required_tools=['schedule_task', 'send_message'],
            instructions="## 自动监控\n\n1. 定期检查系统健康状态\n2. 对比阈值判断异常\n3. 触发告警通知\n4. 记录监控日志"),
        SD(name="workflow_runner", description="运行预定义工作流",
            category=SC.AUTOMATION, icon="▶️", required_tools=['run_python', 'run_shell'],
            instructions="## 工作流执行\n\n1. 解析工作流定义\n2. 按步骤执行任务\n3. 处理条件分支\n4. 汇报执行结果"),
        # ── Research skills ─────────────────────────────
        SD(name="cross_session_recall", description="跨会话研究回溯",
            category=SC.RESEARCH, icon="🔍", required_tools=['session_search', 'memory_read'],
            instructions="## 跨会话回溯\n\n1. 搜索历史会话\n2. 提取相关研究发现\n3. 整理知识脉络\n4. 避免重复研究"),

        # ── Build Team / PM skills ─────────────────────────────────────
        SD(name="task_decomposition", description="将复杂任务分解为可执行子任务并分配给团队成员",
            category=SC.GENERAL, icon="📋",
            required_tools=['send_message'],
            config_schema={
                "max_subtasks": {"type": "integer", "default": 10, "description": "最大子任务数"},
                "auto_assign": {"type": "boolean", "default": True, "description": "自动分配给最佳Agent"},
            },
            instructions="## 任务分解\n\n1. 分析任务目标和范围\n2. 识别关键交付物和里程碑\n3. 将任务分解为 3-10 个可执行子任务\n4. 为每个子任务指定负责Agent和优先级\n5. 设置依赖关系和完成标准\n6. 通过 TaskEngine 提交子任务"),
        SD(name="progress_tracking", description="跟踪项目进度、识别风险和阻塞点",
            category=SC.GENERAL, icon="📊",
            required_tools=['read_file', 'send_message'],
            instructions="## 进度跟踪\n\n1. 查询 TaskEngine 获取任务状态\n2. 计算完成率和延迟风险\n3. 识别阻塞任务和依赖链\n4. 生成进度报告\n5. 向相关Agent发送更新"),
        SD(name="blocker_resolution", description="识别和解决项目阻塞问题",
            category=SC.GENERAL, icon="🔓",
            required_tools=['send_message'],
            instructions="## 阻塞解决\n\n1. 分析阻塞原因\n2. 确定解决方案\n3. 协调相关Agent\n4. 重新分配资源\n5. 更新任务状态"),
        # ── Build Team / Researcher skills ─────────────────────────────
        SD(name="requirements_analysis", description="分析需求文档，提取功能和非功能需求",
            category=SC.GENERAL, icon="📝",
            required_tools=['read_file', 'web_search'],
            instructions="## 需求分析\n\n1. 阅读需求文档\n2. 提取功能需求清单\n3. 识别非功能需求\n4. 标记歧义和缺失项\n5. 生成需求矩阵"),
        # ── Build Team / Architect skills ──────────────────────────────
        SD(name="architecture_design", description="设计系统架构，定义分层和模块边界",
            category=SC.GENERAL, icon="🏗",
            required_tools=['read_file', 'write_file'],
            instructions="## 架构设计\n\n1. 分析需求和约束\n2. 选择架构风格\n3. 定义模块边界和接口\n4. 绘制架构图\n5. 编写 ADR 文档"),
        SD(name="interface_definition", description="定义模块间API接口和数据契约",
            category=SC.GENERAL, icon="🔌",
            required_tools=['write_file', 'read_file'],
            instructions="## 接口定义\n\n1. 确定通信协议\n2. 定义请求/响应模型\n3. 编写 OpenAPI/JSON Schema\n4. 生成接口文档"),
        SD(name="pattern_selection", description="选择适合的设计模式和技术方案",
            category=SC.GENERAL, icon="🧩",
            required_tools=['web_search', 'read_file'],
            instructions="## 模式选择\n\n1. 分析问题场景\n2. 匹配候选设计模式\n3. 评估优劣权衡\n4. 记录选型理由"),
        # ── Build Team / Developer skills ──────────────────────────────
        SD(name="code_implementation", description="编写功能代码，实现需求规格",
            category=SC.GENERAL, icon="💻",
            required_tools=['run_shell', 'write_file', 'read_file'],
            config_schema={
                "executor": {"type": "string", "default": "claude_code",
                    "enum": ["claude_code", "llm_chat", "manual"],
                    "description": "执行器: claude_code=本地Claude Code, llm_chat=LLM生成, manual=手动编码"},
                "claude_code_path": {"type": "string", "default": "claude",
                    "description": "[deprecated] Claude Code CLI 路径——XC-1 后不再使用，保留仅供 AG_ENABLE_LOCAL_CLI=1 逃生舱"},
                "working_directory": {"type": "string", "default": "",
                    "description": "工作目录 (空=项目根)"},
                "auto_test": {"type": "boolean", "default": True,
                    "description": "实现后自动运行测试"},
                "language": {"type": "string", "default": "python",
                    "enum": ["python", "javascript", "typescript"],
                    "description": "主要编程语言"},
            },
            config={
                "executor": "claude_code",
                "claude_code_path": "claude",
                "working_directory": "",
                "auto_test": True,
                "language": "python",
            },
            instructions="## 代码实现\n\n1. 阅读任务描述和架构设计\n2. 确定要修改的文件和模块\n3. 编写实现代码\n4. 运行相关测试确保无回归\n5. 提交代码变更\n\n### 执行器模式\n- **llm_chat** (默认): 通过配置模型 API 生成代码\n- **claude_code** [deprecated]: 仅 AG_ENABLE_LOCAL_CLI=1 时可用\n- **manual**: 生成任务描述供人工编码"),
        SD(name="debugging", description="诊断和修复代码缺陷",
            category=SC.GENERAL, icon="🐛",
            required_tools=['run_shell', 'read_file', 'write_file'],
            instructions="## 调试\n\n1. 复现问题\n2. 分析日志和堆栈\n3. 定位 root cause\n4. 编写修复代码\n5. 验证修复并添加回归测试"),
        SD(name="refactoring", description="重构代码提升可维护性和性能",
            category=SC.GENERAL, icon="♻️",
            required_tools=['read_file', 'write_file', 'run_shell'],
            instructions="## 代码重构\n\n1. 识别代码坏味道\n2. 选择重构策略\n3. 小步修改，保持测试绿色\n4. 验证功能无变化"),
        SD(name="testing", description="编写和执行单元测试",
            category=SC.GENERAL, icon="✅",
            required_tools=['run_shell', 'write_file', 'read_file'],
            instructions="## 测试编写\n\n1. 分析待测代码\n2. 设计测试用例\n3. 编写 pytest 测试\n4. 运行并确认通过"),
        # ── Build Team / Tester skills ─────────────────────────────────
        SD(name="test_design", description="设计测试策略和测试用例",
            category=SC.GENERAL, icon="📐",
            required_tools=['read_file', 'write_file'],
            instructions="## 测试设计\n\n1. 分析功能规格\n2. 设计边界值和等价类\n3. 编写测试矩阵\n4. 确定自动化优先级"),
        SD(name="test_execution", description="执行测试套件并分析结果",
            category=SC.GENERAL, icon="▶️",
            required_tools=['run_shell', 'read_file'],
            instructions="## 测试执行\n\n1. 运行 pytest 测试套件\n2. 收集测试结果\n3. 分析失败用例\n4. 生成测试报告"),
        SD(name="coverage_analysis", description="分析代码覆盖率并识别盲区",
            category=SC.GENERAL, icon="📈",
            required_tools=['run_shell', 'read_file'],
            instructions="## 覆盖率分析\n\n1. 运行 pytest --cov\n2. 分析行覆盖和分支覆盖\n3. 识别未覆盖代码\n4. 建议补充测试"),
        SD(name="regression_testing", description="回归测试确保修改未引入新缺陷",
            category=SC.GENERAL, icon="🔄",
            required_tools=['run_shell'],
            instructions="## 回归测试\n\n1. 确定修改影响范围\n2. 运行相关测试子集\n3. 全量测试验证\n4. 对比前后结果"),
        # ── Build Team / Deployer skills ───────────────────────────────
        SD(name="build_automation", description="自动化构建和打包流程",
            category=SC.GENERAL, icon="🔨",
            required_tools=['run_shell', 'write_file'],
            instructions="## 构建自动化\n\n1. 配置构建脚本\n2. 执行构建命令\n3. 验证产物完整性\n4. 生成构建报告"),
        SD(name="container_management", description="Docker容器构建和管理",
            category=SC.GENERAL, icon="🐳",
            required_tools=['run_shell', 'write_file'],
            instructions="## 容器管理\n\n1. 编写 Dockerfile\n2. 构建镜像\n3. 管理容器生命周期\n4. 配置网络和卷"),
        SD(name="deployment_orchestration", description="编排部署流程和环境管理",
            category=SC.GENERAL, icon="🚀",
            required_tools=['run_shell', 'write_file', 'read_file'],
            instructions="## 部署编排\n\n1. 选择部署策略\n2. 配置环境变量\n3. 执行部署脚本\n4. 验证服务状态"),
        # ── Build Team / Doc Writer skills ─────────────────────────────
        SD(name="technical_writing", description="编写技术文档和开发指南",
            category=SC.GENERAL, icon="📖",
            required_tools=['read_file', 'write_file'],
            instructions="## 技术写作\n\n1. 阅读源代码和注释\n2. 整理技术要点\n3. 编写开发者文档\n4. 添加示例代码"),
        SD(name="api_documentation", description="生成和维护 API 文档",
            category=SC.GENERAL, icon="📄",
            required_tools=['read_file', 'write_file'],
            instructions="## API 文档\n\n1. 扫描 API 端点\n2. 提取参数和返回值\n3. 编写使用示例\n4. 生成 OpenAPI 规格"),
        SD(name="changelog_management", description="维护变更日志和版本记录",
            category=SC.GENERAL, icon="📝",
            required_tools=['read_file', 'write_file'],
            instructions="## 变更日志\n\n1. 收集代码变更\n2. 按类别分组\n3. 编写变更描述\n4. 更新版本号"),
    ]


class SkillRegistry:
    """Runtime registry for managing skills."""

    def __init__(self) -> None:
        self._skills: Dict[str, SkillDefinition] = {}

    def load_defaults(self) -> None:
        """Load all default skills into the registry."""
        for skill in get_default_skills():
            self._skills[skill.skill_id] = skill

    def register(self, skill: SkillDefinition) -> None:
        """Register a single skill."""
        self._skills[skill.skill_id] = skill

    def get(self, skill_id: str) -> Optional[SkillDefinition]:
        """Get a skill by ID."""
        return self._skills.get(skill_id)

    def list_all(self) -> List[SkillDefinition]:
        """Return all registered skills."""
        return list(self._skills.values())

    def list_by_category(self, category: SkillCategory) -> List[SkillDefinition]:
        """Return skills filtered by category."""
        return [s for s in self._skills.values() if s.category == category]

    def list_required(self) -> List[SkillDefinition]:
        """Return only required skills."""
        return [s for s in self._skills.values() if s.required]

    def list_enabled(self) -> List[SkillDefinition]:
        """Return only enabled skills."""
        return [s for s in self._skills.values() if s.enabled]

    def enable(self, skill_id: str) -> bool:
        """Enable a skill."""
        skill = self._skills.get(skill_id)
        if skill is not None:
            skill.enabled = True
            return True
        return False

    def disable(self, skill_id: str) -> bool:
        """Disable a skill."""
        skill = self._skills.get(skill_id)
        if skill is not None:
            skill.enabled = False
            return True
        return False

    def get_by_slug(self, slug: str) -> Optional[SkillDefinition]:
        """Find a skill by slug (URL-safe name)."""
        for s in self._skills.values():
            if s.slug == slug or s.name == slug:
                return s
        return None

    def get_instructions(self, skill_id: str) -> str:
        """Get the instruction text for a skill."""
        skill = self._skills.get(skill_id)
        return skill.instructions if skill else ""

    def get_required_tools(self, skill_id: str) -> List[str]:
        """Get the tool IDs required by a skill."""
        skill = self._skills.get(skill_id)
        return list(skill.required_tools) if skill else []

    def search(self, query: str) -> List[SkillDefinition]:
        """Search skills by name or description."""
        q = query.lower()
        return [
            s for s in self._skills.values()
            if q in s.name.lower() or q in s.description.lower()
        ]

    def create_skill(self, name: str, description: str = "",
                     category: SkillCategory = SkillCategory.GENERAL,
                     instructions: str = "",
                     required_tools: Optional[List[str]] = None) -> SkillDefinition:
        """Create and register a new skill at runtime (Clawith-style skill_manage)."""
        skill = SkillDefinition(
            name=name,
            description=description,
            category=category,
            instructions=instructions,
            required_tools=required_tools or [],
            source="runtime",
        )
        self._skills[skill.skill_id] = skill
        return skill

    def patch_skill(self, skill_id: str, **updates: Any) -> Optional[SkillDefinition]:
        """Patch an existing skill's fields (Hermes skill_manage action=patch)."""
        skill = self._skills.get(skill_id)
        if skill is None:
            return None
        for key, value in updates.items():
            if hasattr(skill, key) and key not in ("skill_id",):
                setattr(skill, key, value)
        return skill

    def delete_skill(self, skill_id: str) -> bool:
        """Delete a skill from the registry."""
        return self._skills.pop(skill_id, None) is not None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize registry to dict."""
        return {sid: s.to_dict() for sid, s in self._skills.items()}

    # ── File-Based Skill Management (Clawith-style) ─────────

    def get_skill_folder(self, skill_id: str) -> Dict[str, Any]:
        """Get a skill's file structure — mirrors Clawith skill browse.

        Returns dict with 'files' list of {path, content} entries.
        """
        skill = self._skills.get(skill_id) or self.get_by_slug(skill_id)
        if skill is None:
            return {"error": "Skill not found", "files": []}

        # Build a SKILL.md from instructions
        files = []
        if skill.instructions:
            files.append({
                "path": "SKILL.md",
                "content": self._build_skill_md(skill),
            })
        return {
            "skill_id": skill.skill_id,
            "name": skill.name,
            "folder_name": skill.slug or skill.name,
            "files": files,
        }

    def import_from_instructions(
        self,
        name: str,
        skill_md_content: str,
        category: SkillCategory = SkillCategory.GENERAL,
    ) -> SkillDefinition:
        """Import a skill from SKILL.md content — mirrors Clawith URL import.

        Parses the SKILL.md frontmatter and body.
        """
        # Parse frontmatter
        description = ""
        icon = "📋"
        required_tools: List[str] = []
        instructions = skill_md_content

        lines = skill_md_content.split("\n")
        if lines and lines[0].strip() == "---":
            end_idx = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    end_idx = i
                    break
            if end_idx > 0:
                # Parse YAML-like frontmatter
                for line in lines[1:end_idx]:
                    if ":" in line:
                        key, _, val = line.partition(":")
                        key = key.strip().lower()
                        val = val.strip()
                        if key == "description":
                            description = val
                        elif key == "icon":
                            icon = val
                        elif key == "name" and val:
                            name = val
                instructions = "\n".join(lines[end_idx + 1:]).strip()

        return self.create_skill(
            name=name,
            description=description,
            category=category,
            instructions=instructions,
            required_tools=required_tools,
        )

    def classify_portability(self, skill_id: str) -> int:
        """Classify skill portability tier — mirrors Clawith portability check.

        Returns:
            1 = pure prompt skill (no external deps)
            2 = CLI/API skill (needs tools)
            3 = platform-native skill (needs specific runtime)
        """
        skill = self._skills.get(skill_id)
        if skill is None:
            return 1

        content = skill.instructions.lower()

        # Tier 3: platform-specific
        platform_markers = ["channel.", "marine_base", "process_event", "digital_twin"]
        if any(m in content for m in platform_markers):
            return 3

        # Tier 2: needs tools/CLI
        cli_markers = ["run_python", "run_shell", "web_search", "python3", "pip install"]
        if any(m in content for m in cli_markers) or skill.required_tools:
            return 2

        # Tier 1: pure prompt
        return 1

    def export_all_as_markdown(self) -> str:
        """Export all skills as a single markdown document."""
        sections = ["# AgentsGroup2026 Skill Registry", ""]
        for skill in sorted(self._skills.values(), key=lambda s: (s.category.value, s.name)):
            tier = self.classify_portability(skill.skill_id)
            sections.append(f"## {skill.icon} {skill.name} (Tier {tier})")
            sections.append(f"**Category**: {skill.category.value}")
            sections.append(f"**Description**: {skill.description}")
            if skill.required_tools:
                sections.append(f"**Required Tools**: {', '.join(skill.required_tools)}")
            sections.append("")
            if skill.instructions:
                sections.append(skill.instructions)
            sections.append("")
            sections.append("---")
            sections.append("")
        return "\n".join(sections)

    @staticmethod
    def _build_skill_md(skill: SkillDefinition) -> str:
        """Build a SKILL.md file content from a SkillDefinition."""
        parts = [
            "---",
            f"name: {skill.name}",
            f"description: {skill.description}",
            f"category: {skill.category.value}",
            f"icon: {skill.icon}",
        ]
        if skill.required_tools:
            parts.append(f"required_tools: {', '.join(skill.required_tools)}")
        parts.append("---")
        parts.append("")
        parts.append(skill.instructions)
        return "\n".join(parts)
