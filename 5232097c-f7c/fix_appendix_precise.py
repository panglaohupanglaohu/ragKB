# -*- coding: utf-8 -*-
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
P=Path('/Users/panglaohu/Downloads/协商审议_DARTNet_记忆遗传_统一闭环论文_架构深化版.docx')
doc=Document(P);body=doc.element.body;children=list(body)
appendix=[];ref=None;conclusion=None
for el in children:
    if el.tag!=qn('w:p'):continue
    txt=''.join(el.itertext())
    if txt.startswith('附录A 工程部署架构') or txt.startswith('AgentsGroup2026以Kubernetes部署') or txt.startswith('Token治理子系统在每次LLM调用前'):
        appendix.append(el)
    if txt.startswith('本文提出一种面向多智能体团队的统一技能生命周期框架'): conclusion=el
    if '参 考 文 献' in txt:ref=el
if len(appendix)!=3 or conclusion is None or ref is None:raise RuntimeError((len(appendix),conclusion,ref))
for el in appendix:body.remove(el)
idx=body.index(ref)
for el in appendix:body.insert(idx,el);idx+=1
doc.save(P);print('fixed precise')
