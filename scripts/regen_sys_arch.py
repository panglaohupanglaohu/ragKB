# -*- coding: utf-8 -*-
"""Regen fig4 — Chinese closed-loop architecture diagram."""
import os, sys
sys.path.insert(0, '/tmp/fig_venv/lib/python3.14/site-packages')
import matplotlib
matplotlib.use('Agg')
import matplotlib.font_manager as fm; fm._load_fontmanager(try_read_cache=False)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.rcParams['font.sans-serif'] = ['Heiti SC']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 9

outdir = "/Users/panglaohu/Downloads/AgentsGroup2026/paper/figures"
os.makedirs(outdir, exist_ok=True)

fig, ax = plt.subplots(figsize=(9, 6.5))
ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.axis('off')

nodes = [
    (5.0, 7.0, 'Plaza协商审议', '#2878B5', 'ORID四层议程\n12-Niche布局\n仪式信号+五指共识', '#E8F0FE'),
    (8.0, 5.5, 'DART-Net技能萃取', '#32B897', '三级层次化编码\nTCN膨胀卷积\n跨模态注意力', '#E8F8F4'),
    (8.0, 3.0, '技能索引与赋予', '#E8913A', '三池分类\nSkillRouter\n两阶段检索', '#FDF0E0'),
    (5.0, 1.5, '任务执行与反馈', '#7B5EA7', 'usage记录\n适应度评估\nReward+老化', '#F0E8F8'),
    (2.0, 3.0, '技能演化与验证', '#E24B4B', '四类变异\n选择性退役\n沙箱验证', '#FDE8E8'),
    (2.0, 5.5, '记忆核心与遗传', '#D4A017', '四层记忆\nSeal-Will-Export-Import\n100% Schema完整性', '#FDF8E0'),
]
for cx, cy, title, color, desc, bg in nodes:
    rect = mpatches.FancyBboxPatch((cx-1.3, cy-0.65), 2.6, 1.3, boxstyle="round,pad=0.15", fc=bg, ec=color, lw=2.0, alpha=0.9)
    ax.add_patch(rect)
    ax.text(cx, cy+0.25, title, ha='center', va='center', fontsize=9, fontweight='bold', color=color)
    ax.text(cx, cy-0.30, desc, ha='center', va='center', fontsize=6.5, color='#555', linespacing=1.3)

arrows = [(5.0,6.35,8.0,6.15),(8.0,4.85,8.0,3.65),(8.0,2.35,5.0,2.15),(5.0,2.15,2.0,2.35),(2.0,3.65,2.0,4.85),(2.0,6.15,5.0,6.35)]
labels = ['审议转录','结构化技能JSON','SkillRouter赋予','执行轨迹+Reward','usage+适应度','记忆经验反馈']
lpos = [(6.5,6.4,0),(8.4,4.25,0),(6.5,2.15,0),(3.5,2.2,0),(1.6,4.25,0),(3.5,6.4,0)]
for (x1,y1,x2,y2), lab, (mx,my,rot) in zip(arrows, labels, lpos):
    ax.annotate("", xy=(x2,y2), xytext=(x1,y1), arrowprops=dict(arrowstyle="->",lw=1.8,color='#555',connectionstyle="arc3,rad=0.15"))
    ax.text(mx, my, lab, fontsize=6.5, color='#777', ha='center', va='center', style='italic')

circle = plt.Circle((5.0,4.25), 1.0, fc='#F8F9FA', ec='#333', lw=1.5, ls='--', alpha=0.6)
ax.add_patch(circle)
ax.text(5.0, 4.25, '技能闭环\n生命周期', ha='center', va='center', fontsize=9, fontweight='bold', color='#333')

ax.annotate("", xy=(3.3,6.5), xytext=(3.3,5.0), arrowprops=dict(arrowstyle="->",lw=1.5,color='#D4A017',ls='dashed',connectionstyle="arc3,rad=-0.3"))
ax.text(2.5, 5.75, '记忆回注', fontsize=6.5, color='#D4A017', ha='center', bbox=dict(boxstyle='round,pad=0.2',fc='#FDF8E0',ec='#D4A017',lw=1))

for cx,cy,lab,cl in [(6.2,5.9,'C_{P→D}','#2878B5'),(7.8,4.3,'C_{D→S}','#32B897'),(6.2,2.5,'C_{S→M}','#7B5EA7'),(3.8,2.5,'C_{M→P}','#D4A017')]:
    ax.text(cx,cy,lab,fontsize=7,color=cl,ha='center',fontweight='bold',bbox=dict(boxstyle='round,pad=0.15',fc='white',ec=cl,lw=0.8,alpha=0.8))

ax.set_title('闭环技能生命周期总体架构', fontsize=13, fontweight='bold', pad=12, color='#222')

outpath = os.path.join(outdir, 'fig4_sys_arch.png')
plt.savefig(outpath, facecolor='white', edgecolor='none', dpi=200)
plt.close()
for f in ['fig1_plaza_niche.png','fig2_dart_arch.png','fig4_sys_arch.png']:
    p = os.path.join(outdir, f)
    if os.path.exists(p):
        print(f"{f}: {os.path.getsize(p)/1024:.0f}KB")
print("Done")
