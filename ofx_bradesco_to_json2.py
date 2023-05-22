#!/usr/bin/env python3
import sys
import json
import os


uninteresting_chars = ["\n", "\t", "\r"]
tags_that_must_be_lists = ["STMTTRN"]


def yield_every_char_from_file(filename):
    with open(filename) as stream:
        while True:
            char = stream.read(1)
            if not char:
                break
            yield char


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
    bank_trans_list = result["OFX"]["BANKMSGSRSV1"]["STMTTRNRS"]["STMTRS"][
        "BANKTRANLIST"
    ]
    new_stmttrn = []

    for _, value in bank_trans_list["STMTTRN"].items():
        new_stmttrn.append(value)

    bank_trans_list["STMTTRN"] = new_stmttrn
    return result


def ofx_bradesco_to_json(filename):
    counter = 0
    result = {"_header": {}}
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
                        counter += 1
                    value_mode = next_char != "<"
                    current_string = ""
                continue
            current_string += char
    result = fix_stmtrn(result)
    return result


def _get_target_filename(input_file_name, ignore_sysargv):
    if ignore_sysargv or len(sys.argv) <= 2:
        return input_file_name[0 : input_file_name.rfind(".")] + ".json"
    else:
        return sys.argv[2]


def save_output_to_disk(input_filename, result, ignore_sysargv=False):
    output_filename = _get_target_filename(input_filename, ignore_sysargv)
    with open(output_filename, "w") as output_file:
        json.dump(result, output_file, indent=2, ensure_ascii=False)
    print(f"{input_filename} saved to {output_filename}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or not os.path.isfile(sys.argv[1]):
        print(
            f"usage: {sys.argv[0]} ofx_to_become_a_json.ofx [optional_output_name.json]"
        )
        sys.exit(1)

    input_filename = sys.argv[1]
    result = ofx_bradesco_to_json(input_filename)
    # dumper(result)
    save_output_to_disk(input_filename, result)
