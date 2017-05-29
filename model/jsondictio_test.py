#!/usr/bin/env python
# -*- coding: utf8 -*-

import unittest

from jsondictio import JSONDictIO
import io
import tempfile, os

class JSONDictIOTestCase(unittest.TestCase):
    def test_io_on_string(self): 
        # prepare a JSON string
        text_io = io.StringIO()
        text_io.write(u'{"i1": {"ï11": "ěščřžýáíé", "i12": "v12"}, "i2": "v2"}')
        dict_io = JSONDictIO(text_io)

        # get()
        d = dict_io.get()
        self.assertEqual(d, {"i1": {u"ï11": u"ěščřžýáíé", "i12": "v12"}, "i2": "v2"})

        # modify the dict
        d['i1']['i13'] = 'v13'  # add an item
        d['i1'][u'ï11'] = u'něw válůé' # modify an existing item

        # set(), then get() and check
        dict_io.set(d)
        new_d = dict_io.get()
        
        #print "    d:", d
        #print "new_d:", new_d
        self.assertEqual(new_d, {"i1": {u"ï11": u"něw válůé", "i12": "v12", "i13": "v13"}, "i2": "v2"})
    

    def test_io_on_file(self): 
        # create a temp file
        f = tempfile.NamedTemporaryFile(delete=False)
        f.close()

        # fill the temp file
        f_io = io.open(f.name, mode='w', encoding='utf-8')
        f_io.write(u'{"i1": {"ï11": "ěščřžýáíé", "i12": "v12"}, "i2": "v2"}')
        f_io.close()

        # load the content of the file to a dict, check, modify, save, load again, check
        with io.open(f.name, mode='r+', encoding='utf-8') as text_io: 
            dict_io = JSONDictIO(text_io)
            d = dict_io.get()
            
            self.assertEqual(d, {"i1": {u"ï11": u"ěščřžýáíé", "i12": "v12"}, "i2": "v2"})

            d['i1']['i13'] = 'v13'  # add an item
            d['i1'][u'ï11'] = u'něw válůé' # modify an existing item

            dict_io.set(d)

            new_d = dict_io.get()
            self.assertEqual(new_d, {"i1": {u"ï11": u"něw válůé", "i12": "v12", "i13": "v13"}, "i2": "v2"})

        # the file has been closed; open it again and see if the modified dict is there
        with io.open(f.name, mode='r+', encoding='utf-8') as text_io: 
            dict_io = JSONDictIO(text_io)
            new_d = dict_io.get()
            self.assertEqual(new_d, {"i1": {u"ï11": u"něw válůé", "i12": "v12", "i13": "v13"}, "i2": "v2"})

        # delete the temp file
        os.unlink(f.name)


if __name__ == '__main__': 
    unittest.main()
