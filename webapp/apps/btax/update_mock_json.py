import json
import random

with open('__mock_btax_result.json') as f:
    data = f.read()
    data = json.loads(data)

cats = ['Major Grouping 1',
        'Major Grouping 2',
        'Major Grouping 3',
        'Major Grouping 4',
        'Major Grouping 5',
        'Major Grouping 6']

for h in list(data.keys()):
    if h.startswith('asset') or h.startswith('industry'):
        for i in list(data[h].keys()):
            for j in data[h][i]['rows']:
                j['major_grouping'] = random.choice(cats)
                j['summary_c'] = -999
                j['summary_nc'] = -999
    
with open('mock_btax_result.json','w') as f:
    f.write(json.dumps(data))
