"""Small synthetic retrieval regression check, not a general quality claim."""
import json
from pathlib import Path
from app.core import search
CORPUS = [
 {'text':'Solar panels supply electricity to the community centre.', 'page':1},
 {'text':'Bicycle repair workshops teach volunteers to maintain bicycles.', 'page':2},
 {'text':'Food collection supports a neighbourhood pantry.', 'page':3},
 {'text':'مبادرة إعادة التدوير لحماية البيئة وتقليل النفايات', 'page':4}]
CASES = [('solar electricity',1),('bicycle repair',2),('food collection',3),('اعادة التدوير',4)]
rows=[]
for question, expected in CASES:
    hits=search(CORPUS,question)
    actual=hits[0]['page'] if hits else None
    rows.append({'query':question,'expected_page':expected,'actual_page':actual,'correct':actual==expected})
result={'scope':'4 synthetic lexical queries; not representative of real-world performance', 'top1_accuracy':sum(r['correct'] for r in rows)/len(rows),'cases':rows}
Path('docs/evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
assert all(row['correct'] for row in rows), 'Synthetic retrieval regression failed'
