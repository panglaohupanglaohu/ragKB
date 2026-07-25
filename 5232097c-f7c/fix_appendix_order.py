# -*- coding: utf-8 -*-
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn

P=Path('/Users/panglaohu/Downloads/协商审议_DARTNet_记忆遗传_统一闭环论文_架构深化版.docx')
doc=Document(P)
body=doc.element.body
children=list(body)
start=end=ref=None
for i,el in enumerate(children):
    if el.tag==qn('w:p'):
        txt=''.join(el.itertext())
        if txt.startswith('附录A 工程部署架构'): start=i
        if start is not None and '参 考 文 献' in txt:
            end=i; ref=el; break
if start is None or end is None:
    raise RuntimeError('appendix block not found')
block=children[start:end]
for el in block:
    body.remove(el)
# insert before references, after conclusion body
idx=body.index(ref)
for el in block:
    body.insert(idx,el); idx+=1
doc.save(P)
print('fixed',P)
