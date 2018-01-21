#!/usr/bin/env python
import os
import sys
import json
import codecs
from collections import OrderedDict

LINE_OTHER = 0
LINE_OPEN_TAG = 1
LINE_CLOSE_TAG = 2
LINE_SINGLE_LINE_TAG = 3

gap_count = 0
gap = "  "

ast_line_type = this_line_type = LINE_OTHER

def parse_line(line):
    if line.startswith("</"):
        return LINE_CLOSE_TAG
    if line.startswith("<") and line.endswith(">"):
        return LINE_OPEN_TAG
    if line.startswith("<"):
        return LINE_SINGLE_LINE_TAG
    return LINE_OTHER

if not os.path.isfile(sys.argv[1]):
    print("usage: {sys.argv[0]} ofx_to_become_a_json.ofx [converted_ofx.json]")
    sys.exit(1)

target_json = OrderedDict()
target_json["_header"] = OrderedDict()

dict_list = [target_json]

input_file_name = sys.argv[1]

#with open(sys.argv[1], "r") as input_file:
with codecs.open(sys.argv[1], 'r', 'iso-8859-1') as input_file:
    while True:
        input_line = input_file.readline()
        if input_line == "": # is None or input_line is False:
            print("done")
            break

        input_line = input_line.strip()
        last_line_type = this_line_type
        this_line_type = parse_line(input_line)

        if input_line == "":
            continue

        if this_line_type == LINE_OTHER:
            key, value = input_line.split(":")
            target_json["_header"][key] = value
        elif this_line_type == LINE_OPEN_TAG:
            tag_name = input_line[1:-1]
            new_json = OrderedDict()

            if tag_name in dict_list[-1]:
                if not isinstance(dict_list[-1][tag_name], list):
                    old_elem = dict_list[-1][tag_name]
                    dict_list[-1][tag_name] = [ old_elem ]

                dict_list[-1][tag_name].append(new_json)

            else:
                dict_list[-1][tag_name] = new_json
            dict_list.append(new_json)

        elif this_line_type == LINE_CLOSE_TAG:
            dict_list.pop()

        elif this_line_type == LINE_SINGLE_LINE_TAG:
            pos = input_line.find(">")
            key = input_line[1:pos]
            value = input_line[pos+1:]

            dict_list[-1][key] = value

        else:
            print("Invalid line type: [{}]".format(this_line_type))
            sys.exit(1)





if len(sys.argv) <= 2:
    target_file = input_file_name[0:input_file_name.rfind(".")] + ".json"
else:
    target_file = sys.argv[2]

result = json.dumps(target_json, indent=2) #, sort_keys=True)

with open(target_file, "w") as output_file:
    output_file.write(result)
