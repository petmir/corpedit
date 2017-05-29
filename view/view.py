#!/usr/bin/env python
# -*- coding: utf8 -*-

import xyaptu
from compiler import compile_template

OUTPUT_MODE_PLAIN = 'plain'  # TODO: how to handle cookies in plain mode?
OUTPUT_MODE_CGI = 'cgi'
output_mode = OUTPUT_MODE_CGI

DATA_TYPE_PAGE = 'page'
DATA_TYPE_REDIRECT = 'redirect'
DATA_TYPE_AJAX_CONTENT = 'ajax_content'
DATA_TYPE_TERMINAL_OUTPUT = 'terminal_output'

def set_output_mode(m): 
    global output_mode

    output_mode = m


def get_output(data_type, data): 
    global output_mode

    if data_type == DATA_TYPE_PAGE: 
        if output_mode == OUTPUT_MODE_CGI: 
            output = "Content-type: text/html\n"
            output += "Set-Cookie:%s=%s\n" % ('session_id', data['session_id'])  
            # TODO: instead of 'session_id' here, how to import the COOKIE_SESSION_ID constant from controller.py?
            output += "\n"
        else: 
            output = ""

        if data['page_type'] == 'home':
            output += compile_template('view/home.template', data)  # NOTE: why is "view/" necessary?
        if data['page_type'] == 'admin':
            output += compile_template('view/admin.template', data)
        elif data['page_type'] == 'window': 
            output += compile_template('view/window.template', data)
        elif data['page_type'] == 'error': 
            output += compile_template('view/error.template', data)

    elif data_type == DATA_TYPE_AJAX_CONTENT: 
        output = "Content-type: text/html\n"
        output += "\n"
        output += data

    elif data_type == DATA_TYPE_REDIRECT: 
        output = "Location: %s\n\n" % data

    elif data_type == DATA_TYPE_TERMINAL_OUTPUT: 
        output = "Content-type: text/html\n"
        output += "\n"
        output += compile_template('view/admin_terminal_output.template', data)

    else: 
        raise Exception('invalid data type')

    return output

