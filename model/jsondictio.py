#!/usr/bin/env python
# -*- coding: utf8 -*-

import json

class JSONDictIO:

    # text_io should be a stream such as an instance of io.TextIOBase; 
    # it must be a finite stream that supports random access
    # (get() reads all the content, set() replaces it); 
    # it must support unicode
    def __init__(self, text_io): 
        self._io = text_io

    def get(self): 
        # returns everything (if it's a JSON object) as a dict
        self._io.seek(0)
        json_string = self._io.read(None)  # read all the stream until EOF
        return json.JSONDecoder().decode(json_string)

    def set(self, d): 
        # overwrites everything with a dict
        self._io.seek(0)
        self._io.truncate()
        json_string = unicode(json.JSONEncoder().encode(d))
        self._io.write(json_string)

