#!/usr/bin/env python
# -*- coding: utf8 -*-

import difflib

def no_context_diff(data1, data2): 
    data1_lines = data1.rstrip(os.linesep).split(os.linesep)
    data2_lines = data2.rstrip(os.linesep).split(os.linesep)

    # add a trailing newline to each line for difflib.unified_diff()
    for i in range(0, len(data1_lines)):
        data1_lines[i] += os.linesep
    for i in range(0, len(data2_lines)):
        data2_lines[i] += os.linesep

    diff_line_generator = difflib.unified_diff(data1_lines, data2_lines, n=0)
    d = u''
    for diff_line in diff_line_generator: 
        if not (diff_line.startswith('+++') or diff_line.startswith('---')): 
            d += diff_line

    return d

if __name__== # TODO
