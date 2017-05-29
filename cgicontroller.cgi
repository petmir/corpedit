#!/usr/bin/env python
# -*- coding: utf8 -*-


import cgi, cgitb
cgitb.enable() # for debugging
from os import environ # for cookies

from string import strip, split

from view import view
import controller


if __name__ == '__main__': 
    cgi_args = cgi.FieldStorage() # URL query string args, can be used as a dictionary

    # convert URL args to a dict 
    request_args = dict()
    for i in cgi_args: 
        request_args[i] = cgi_args.getvalue(i)

    #print "Content-type: text/html\n";

    # convert cookies to a dict
    request_cookies = dict()
    if environ.has_key('HTTP_COOKIE'): 
        for cookie in map(strip, split(environ['HTTP_COOKIE'], ';')):
            (key, value) = split(cookie, '=')
            request_cookies[key] = value

    result = controller.run(request_args, request_cookies)
    assert result is not None
    view.set_output_mode(view.OUTPUT_MODE_CGI)
    output = view.get_output(result['type'], result['data'])  # the view module renders the output
                                                              # depending on its type
    print output
