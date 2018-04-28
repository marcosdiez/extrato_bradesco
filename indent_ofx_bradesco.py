#!/usr/bin/env python
import os
import sys

LINE_OTHER = 0
LINE_OPEN_TAG = 1
LINE_CLOSE_TAG = 2
LINE_SINGLE_LINE_TAG = 3

gap_count = 0
gap = "  "

ast_line_type = this_line_type = LINE_OTHER

def write_to_output(output_file, input_line):
    for i in range(0, gap_count):
        output_file.write(gap)
    output_file.write(input_line)
    output_file.write("\n")

def parse_line(line):
    if line.startswith("</"):
        return LINE_CLOSE_TAG
    if line.startswith("<") and "</" in line:
        return LINE_SINGLE_LINE_TAG
    if line.startswith("<") and line.endswith(">"):
        return LINE_OPEN_TAG
    if line.startswith("<"):
        return LINE_SINGLE_LINE_TAG
    return LINE_OTHER

if not os.path.isfile(sys.argv[1]):
    print("usage: {sys.argv[0]} file_to_be_indented.ofx")
    sys.exit(1)

with open(sys.argv[1], "r") as input_file:
    with open(sys.argv[1][0:-4] + "_indent.ofx", "w") as output_file:
        while True:
            input_line = input_file.readline()
            if input_line == "": # is None or input_line is False:
                print("done")
                sys.exit(0)

            input_line = input_line.strip()
            last_line_type = this_line_type
            this_line_type = parse_line(input_line)

            if this_line_type == LINE_OTHER:
                write_to_output(output_file, input_line)
            elif this_line_type == LINE_OPEN_TAG:
                write_to_output(output_file, input_line)
                gap_count += 1
            elif this_line_type == LINE_CLOSE_TAG:
                gap_count -= 1
                write_to_output(output_file, input_line)
            elif this_line_type == LINE_SINGLE_LINE_TAG:
                write_to_output(output_file, input_line)
            else:
                print("Invalid line type: [{}]".format(this_line_type))
                sys.exit(1)







