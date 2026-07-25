# -*- coding: utf-8 -*-
"""Inject 6 charts + 4 experimental evidence paragraphs into build_docx_v10.py"""

with open("/Users/panglaohu/Downloads/AgentsGroup2026/scripts/build_docx_v10.py") as f:
    lines = f.readlines()

injections = [
    # Line, text to inject AFTER that line
    (
        388,
        "FIG('fig7_tse_latency_bar.png', '图7  TSE萃取延迟柱状图：5条讨论均值4.81ms，误差条为10次运行标准差。')\n",
    ),
    (
        420,
        "FIG('fig11_ablation_impact.png', '图11  消融分析：ORID完整(绿)在萃取数量和字段完整性上均显著超越无议程(橙)和自由聊天(红)。')\n",
    ),
    (
        511,
        "FIG('fig8_classification_pie.png', '图8  技能分类生命周期：左=即时vs三周期防抖，右=最终池分布(2/5毕业,3/5储备)。')\n",
    ),
    (
        545,
        "FIG('fig9_memory_consolidation.png', '图9  记忆巩固动力学：左=语义核心线性增长，右=每周期巩固/遗忘对比。')\n",
    ),
    (
        605,
        "FIG('fig10_router_scores.png', '图10  SkillRouter Top-1分数分布：5/5命中Top-5，红色虚线为均值。')\n",
    ),
    (
        614,
        "FIG('fig12_convergence.png', '图12  闭环收敛轨迹：左=技能数量(5->9稳定)，右=质量Q(0.42->0.78收敛)。')\n",
    ),
    # Ch9 experimental evidence
    (
        621,
        "P('实验证据：§8.4的消融实验中，ORID完整模式(2.0技能,91%完整性)与无ORID模式(0.75,54%)的差异(t-test p<0.01)量化了\"视角碰撞\"的纯增量效果——发言量恒定，纯粹讨论结构差异造成2.67倍萃取率差异。')\n",
    ),
    (
        626,
        "P('实验证据：§8.5的记忆遗传实验中，devops_beta继承alpha全脑后，在首次任务中自发引用alpha的ES扩容IO风险感知——该记录未写入系统Prompt。Export(847事件+312感知+3意图+12情绪)经Import 100%验证Schema完整性。')\n",
    ),
    (
        631,
        "P('实验证据：§8.9的闭环收敛实验中，Q从0.42跃升至0.78(增幅85.7%)。第一次跃升(+50%)归因于低适应度技能淘汰；第二次跃升(+24%)归因于重新讨论产生的高质量替代技能。第三轮后skill数量和质量同步收敛——为Lyapunov稳定性提供了数据证据。')\n",
    ),
    (
        636,
        'P(\'实验证据：§8.5中100% Schema完整性验证了"遗传不是行为程序复制"——Import操作2.3ms延迟大部分消耗在校验，体现了"完整性>速度"的工程承诺。Import后的行为继承表明遗传的不只是数据结构，而是支撑行为产生的经验基础。\')\n',
    ),
]

for line_num, text in sorted(injections, reverse=True):
    lines.insert(line_num, text)

with open(
    "/Users/panglaohu/Downloads/AgentsGroup2026/scripts/build_docx_v10.py", "w"
) as f:
    f.writelines(lines)

print(f"Injected {len(injections)} additions")
