#!/usr/bin/env python3
import sys
import json


def yield_every_char_from_file(filename):
    with open(filename) as stream:
        while True:
            char = stream.read(1)
            if not char:
                break
            yield char


uninteresting_chars = ["\n", "\t", "\r"]
tags_that_must_be_lists = ["STMTTRN", "/STMTTRN"]

def dumper(obj):
    print(json.dumps(obj, sort_keys=False, indent=2))


def add_to_result(result, tag_stack, value):
    print(f"{tag_stack} = {value}")
    current_position = result
    for tag in tag_stack[0:-1]:
        if tag not in current_position:
            current_position[tag] = {}
        current_position = current_position[tag]
    last_tag = tag_stack[-1]
    current_position[last_tag] = value


def process_ofx(filename):
    counter = 0
    result = {}
    tag_stack = []
    next_char = None
    current_string = ""
    previsous_string = ""
    value_mode = False
    for _char in yield_every_char_from_file(filename):
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
                # print(f"---- {current_string} {previsous_string}")

                previsous_string = current_string
                current_string = ""
                tag_stack.pop()
                if previsous_string in tags_that_must_be_lists:
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


result = process_ofx(sys.argv[1])
dumper(result)
