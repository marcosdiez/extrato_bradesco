#!/usr/bin/env python3
import sys
import json
import os

def yield_every_char_from_file(filename):
    with open(filename) as stream:
        while True:
            char = stream.read(1)
            if not char:
                break
            yield char


uninteresting_chars = ["\n", "\t", "\r"]
tags_that_must_be_lists = ["STMTTRN"]

def dumper(obj):
    print(json.dumps(obj, sort_keys=False, indent=2))


def add_to_result(result, tag_stack, value):
    # print(f"{tag_stack} = {value}")
    current_position = result
    for tag in tag_stack[0:-1]:
        if tag not in current_position:
            current_position[tag] = {}
        current_position = current_position[tag]
    last_tag = tag_stack[-1]
    current_position[last_tag] = value


def fix_stmtrn(result):
    bank_trans_list = result["OFX"]["BANKMSGSRSV1"]["STMTTRNRS"]["STMTRS"]["BANKTRANLIST"]
    new_stmttrn = []

    for key , value in bank_trans_list["STMTTRN"].items():
        new_stmttrn.append(value)

    bank_trans_list["STMTTRN"] = new_stmttrn
    return result

def process_ofx(filename):
    counter = 0
    result = {
        "_header": {}
    }
    tag_stack = []
    next_char = None
    char = None
    current_string = ""
    previsous_string = ""
    value_mode = False

    header_mode = True
    for _char in yield_every_char_from_file(filename):
        if header_mode:
            char = next_char
            next_char = _char
            if char is None:
                # first time only
                continue

            elif char == "\r":
                continue

            elif char == "\n":
                if len(current_string) > 0:
                    key, value = current_string.split(":")
                    result["_header"][key] = value
                    current_string = ""
                continue

            elif char == "<":
                header_mode = False
                continue
            else:
                 current_string += char

        else:
            if _char in uninteresting_chars:
                continue

            char = next_char
            next_char = _char
            if char is None:
                # first time only
                continue

            if char == "<":
                if value_mode:
                    value = current_string
                    add_to_result(result, tag_stack, value)
                    tag_stack.pop()
                previsous_string = current_string
                current_string = ""
                continue

            if char == ">":
                if current_string.startswith("/"):
                    value_mode = False
                    previsous_string = current_string
                    current_string = ""
                    tag_stack.pop()
                    if previsous_string[1:] in tags_that_must_be_lists:
                        tag_stack.pop()
                else:
                    tag_stack.append(current_string)
                    if current_string in tags_that_must_be_lists:
                        tag_stack.append(counter)
                        counter+=1
                    value_mode = next_char != "<"
                    current_string = ""
                continue
            current_string += char
    return result

def _get_target_filename(input_file_name):
    if len(sys.argv) <= 2:
        return input_file_name[0:input_file_name.rfind(".")] + ".json"
    else:
        return sys.argv[2]

if __name__ == "__main__":
    if len(sys.argv) < 2 or not os.path.isfile(sys.argv[1]):
        print("usage: {} ofx_to_become_a_json.ofx [optional_output_name.json]".format(sys.argv[0]))
        sys.exit(1)

    input_filename = sys.argv[1]
    result = process_ofx(input_filename)
    # dumper(result)
    result = fix_stmtrn(result)

    output_filename = _get_target_filename(input_filename)
    with open(output_filename, "w") as output_file:
        json.dump(result, output_file, indent=2, ensure_ascii=False)
    print("{} saved to {}".format(input_filename, output_filename))
