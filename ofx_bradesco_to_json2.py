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

def add_to_result(result, tag_stack, value):
    print(f"{tag_stack} = {value}")

def process_ofx(filename):
    result = {}
    tag_stack = []
    next_char = None
    current_string = ""
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
            current_string = ""
            continue

        if char == ">":
            if current_string.startswith("/"):
                value_mode = False
                current_string=""
                tag_stack.pop()
            else:
                tag_stack.append(current_string)
                value_mode = next_char != "<"
                current_string = ""
            continue
        current_string += char

process_ofx(sys.argv[1])

