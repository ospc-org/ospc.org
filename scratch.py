import json
from pprint import pprint
from collections import OrderedDict


with open("current_law_policy.json", "r") as f:
    a = json.loads(f.read(), object_pairs_hook=OrderedDict)


grouped_fields = []
for x in a:
    section_name = dict(a[x]).get("section_1")
    if section_name:
        section_name = section_name.lower()
        section = next((item for item in grouped_fields if section_name in item.keys()), None)
        if not section:
            grouped_fields.append({section_name: [{x: dict(a[x])}]})
        else:
            section[section_name].append({x: dict(a[x])})

pprint(grouped_fields[0])
