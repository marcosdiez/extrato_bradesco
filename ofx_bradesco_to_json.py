#!/usr/bin/env python
from __future__ import unicode_literals
from __future__ import print_function
import os
import sys
import json
import codecs
from collections import OrderedDict


LINE_OTHER = 0
LINE_OPEN_TAG = 1
LINE_CLOSE_TAG = 2
LINE_SINGLE_LINE_TAG = 3
LINE_BEGIN_MULTI_LINE = 4
LINE_MIDDLE_MULTI_LINE = 5
LINE_END_MULTI_LINE = 6

def enum_to_text(value):
    if value == LINE_OTHER:
        return "LINE_OTHER"
    if value == LINE_OPEN_TAG:
        return "LINE_OPEN_TAG"
    if value == LINE_CLOSE_TAG:
        return "LINE_CLOSE_TAG"
    if value == LINE_SINGLE_LINE_TAG:
        return "LINE_SINGLE_LINE_TAG"
    if value == LINE_BEGIN_MULTI_LINE:
        return "LINE_BEGIN_MULTI_LINE"
    if value == LINE_MIDDLE_MULTI_LINE:
        return "LINE_MIDDLE_MULTI_LINE"
    if value == LINE_END_MULTI_LINE:
        return "LINE_END_MULTI_LINE"
    else:
        raise(ValueError(value))

def _parse_line(line, current_state=None, current_tag=None):
    if line.startswith("<") and not line.endswith(">"):
        return LINE_BEGIN_MULTI_LINE
    if current_state in (LINE_BEGIN_MULTI_LINE, LINE_MIDDLE_MULTI_LINE):
        if "</" in line and line.endswith(">"):
            return LINE_END_MULTI_LINE
        else:
            return LINE_MIDDLE_MULTI_LINE

    if line.startswith("</"):
        return LINE_CLOSE_TAG
    if line.startswith("<") and "</" in line:
        return LINE_SINGLE_LINE_TAG
    if line.startswith("<") and line.endswith(">"):
        return LINE_OPEN_TAG
    if line.startswith("<"):
        return LINE_SINGLE_LINE_TAG
    return LINE_OTHER

def ofx_bradesco_to_json(input_file, debug=True):
    target_json = OrderedDict()
    target_json["_header"] = OrderedDict()
    dict_list = [target_json]
    line_number = 0
    this_line_type = None
    while True:
        input_line = input_file.readline()
        line_number += 1
        try:
            if input_line == "":  # is None or input_line is False:
                break

            input_line = input_line.strip()
            this_line_type = _parse_line(input_line, this_line_type)

            if input_line == "":
                continue

            if debug:
                print("Line {:4}/{:23}: [{}]".format(line_number, enum_to_text(this_line_type), input_line))

            if this_line_type == LINE_OTHER:
                key, value = input_line.split(":")
                target_json["_header"][key] = value
            elif this_line_type == LINE_OPEN_TAG:
                tag_name = input_line[1:-1]
                new_json = OrderedDict()

                if tag_name in dict_list[-1]:
                    if not isinstance(dict_list[-1][tag_name], list):
                        old_elem = dict_list[-1][tag_name]
                        dict_list[-1][tag_name] = [old_elem]

                    dict_list[-1][tag_name].append(new_json)

                else:
                    dict_list[-1][tag_name] = new_json
                dict_list.append(new_json)

            elif this_line_type == LINE_CLOSE_TAG:
                dict_list.pop()

            elif this_line_type == LINE_SINGLE_LINE_TAG:
                pos = input_line.find(">")
                key = input_line[1:pos]
                value = input_line[pos + 1:]

                pos2 = value.find("</")
                if pos2 > 0:
                    value = value[0:pos2]

                dict_list[-1][key] = value
            elif this_line_type == LINE_BEGIN_MULTI_LINE:
                pos = input_line.find(">")
                key = input_line[1:pos]
                value = input_line[pos + 1:]
            elif this_line_type == LINE_MIDDLE_MULTI_LINE:
                value += " " + input_line
            elif this_line_type == LINE_END_MULTI_LINE:
                pos2 = input_line.find("</")
                if pos2 > 0:
                    value += " " + input_line[0:pos2]

                dict_list[-1][key] = value
            else:
                raise ValueError("Invalid line type: [{}]".format(this_line_type))
                sys.exit(1)
        except (ValueError, IndexError) as e:
            print("Error parsing line {}/{}: [{}]".format(line_number, enum_to_text(this_line_type), input_line))
            raise e
    return target_json

def _get_target_filename():
    if len(sys.argv) <= 2:
        return input_file_name[0:input_file_name.rfind(".")] + ".json"
    else:
        return sys.argv[2]

if __name__ == "__main__":
    if len(sys.argv) < 2 or not os.path.isfile(sys.argv[1]):
        print("usage: {} ofx_to_become_a_json.ofx [converted_ofx.json]".format(sys.argv[0]))
        sys.exit(1)

    input_file_name = sys.argv[1]

    with codecs.open(input_file_name, 'r', 'iso-8859-1') as input_file:
        target_json = ofx_bradesco_to_json(input_file)

    target_filename = _get_target_filename()
    with codecs.open(target_filename, "w", "utf-8") as output_file:
        json.dump(target_json, output_file, indent=2, ensure_ascii=False)
    print("{} saved to {}".format(input_file_name, target_filename))

