import json
from pprint import pprint
from collections import OrderedDict


with open("current_law_policy.json", "r") as f:
    a = json.loads(f.read(), object_pairs_hook=OrderedDict)


def parse_sub_category(field_section):
    output = []
    free_fields = []
    for x in field_section:
        for y, z in x.iteritems():
            section_name = dict(z).get("section_2")
            if section_name:
                section_name = section_name.lower()
                section = next((item for item in output if section_name in item), None)
                if not section:
                    output.append({section_name: [{y: dict(z)}]})
                else:
                    section[section_name].append({y: dict(z)})
            else:
                free_fields.append(field_section.pop(field_section.index(x)))
    return output + free_fields

def parse_category(json_output):
    output = []
    for x, y in json_output.iteritems():
        section_name = dict(y).get("section_1")
        if section_name:
            section_name = section_name.lower()
            section = next((item for item in output if section_name in item), None)
            if not section:
                output.append({section_name: [{x: dict(y)}]})
            else:
                section[section_name].append({x: dict(y)})
    return output

b = parse_category(a)[0]
c = parse_sub_category(b.values()[0])
