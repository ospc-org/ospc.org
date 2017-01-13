import json
from pprint import pprint
from collections import OrderedDict


with open("current_law_policy.json", "r") as f:
    a = json.loads(f.read(), object_pairs_hook=OrderedDict)


def parse_sub_category(field_section):
    output_list = []
    for x in field_section:
        print(x)

def parse_category(json_output):
    output = []
    for x in json_output:
        section_name = dict(json_output[x]).get("section_1")
        if section_name:
            section_name = section_name.lower()
            section = next((item for item in output if section_name in item.keys()), None)
            if not section:
                output.append({section_name: [{x: dict(json_output[x])}]})
            else:
                section[section_name].append({x: dict(json_output[x])})
    return output

b = parse_category(a)[0]
c = parse_sub_category(b.values()[0])
