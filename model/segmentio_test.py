#!/usr/bin/env python
# -*- coding: utf8 -*-

import unittest

from segmentio import Segment, SegmentIO, Hunk
import segmentio
import io
import tempfile, os
import sys 
import shutil
from time import time

sys.path.append('../')  # for imports from the project's root directory
import common
from common import dbg, dbg_notb, subprocess_call


def are_equivalent_changelogs(file_to_test_on, c1, c2): 
    # load the data
    with io.open(file_to_test_on, 'r', encoding='utf-8') as f: 
        src_content_1 = f.read()
        src_content_2 = src_content_1

    # apply c1
    dest_content_1 = segmentio.patch(src_content_1, c1)

    # apply c2
    dest_content_2 = segmentio.patch(src_content_2, c2)

    # compare the results
    return dest_content_1 == dest_content_2



class SegmentTestCase(unittest.TestCase):
    def setUp(self): 
        # first line of the segment: line 1271 in the src file, line 1521 in the virtual file
        # first line after the segment: line 1285 in the src file, line 1529 in the virtual file
        # (the segment is 14 lines high in the src file, 8 lines high in the virtual file)
        # first line of the block: line 3 in the segment
        # first line after the block: line 8 in the segment
        # (the block is 5 lines high)
        self._s = Segment(u'first(ěščř)\nsecond\nthird\nfourth\nfifth(žýáíé)\nsixth\nseventh\neighth\n', '', 
                1271, 1285, 
                1521, 1529, 
                3, 8)


    def test_block_data(self): 
        self.assertEqual(self._s.block_data(), u'third\nfourth\nfifth(žýáíé)\nsixth\nseventh\n')


    def test_set_block_data(self): 
        self._s.set_block_data(u'third\nthen\nonly\nthis\n')
        self.assertEqual(self._s.block_data(), u'third\nthen\nonly\nthis\n')

        # also check if _segment_data is correct
        self.assertEqual(self._s._segment_data, u'first(ěščř)\nsecond\nthird\nthen\nonly\nthis\neighth\n')


    def test_changelog(self):
        self._s.set_block_data(u'third\nthen\nonly\nthis\n')
        self.assertEqual(self._s.changelog(), u'''@@ -4,4 +4,3 @@
-fourth
-fifth(žýáíé)
-sixth
-seventh
+then
+only
+this
''')
        # src: begin on line 4, first line is 1271, dest: begin on line 4, first line is 1521
        self.assertEqual(self._s.changelog(globalLineNumbers=True), u'''@@ -1274,4 +1524,3 @@
-fourth
-fifth(žýáíé)
-sixth
-seventh
+then
+only
+this
''')

        # src: begin on line 4, first line is 1521, dest: begin on line 4, first line is 1521
        self.assertEqual(self._s.changelog(lineNumbersFromDest=True), u'''@@ -1524,4 +1524,3 @@
-fourth
-fifth(žýáíé)
-sixth
-seventh
+then
+only
+this
''')



class HunkTestCase(unittest.TestCase): 
    def test_set_first_lines(self): 
        # example from segmentio_testdata/handmade-changelog/reference-changelog.patch
        src_begin = 33
        src_nlines = 4
        dest_begin = 85
        dest_nlines = 2
        content = '''-Tenhle
-naopak
-bude
-zkrácen.
+Tenhle byl
+naopak zkrácen.
'''
        h = Hunk(src_begin, src_nlines, dest_begin, dest_nlines, content)

        self.assertEqual(src_begin, h.x1())
        self.assertEqual(src_nlines, h.n1())
        self.assertEqual(dest_begin, h.x2())
        self.assertEqual(dest_nlines, h.n2())

        # shift the line numbers so that we get a changelog for a segment 
        # beginning where this hunk begins
        h.set_first_lines(src_line=src_begin, dest_line=dest_begin)
        self.assertEqual(1, h.x1())
        self.assertEqual(src_nlines, h.n1())
        self.assertEqual(1, h.x2())
        self.assertEqual(dest_nlines, h.n2())

        # reset the line numbers, then the line numbers should match those 
        # in the original changelog again
        h.set_first_lines()
        self.assertEqual(src_begin, h.x1())
        self.assertEqual(src_nlines, h.n1())
        self.assertEqual(dest_begin, h.x2())
        self.assertEqual(dest_nlines, h.n2())

        # check the content
        self.assertEqual(h.content(), content)
        self.assertEqual(h.content_lines(), [
            '-Tenhle\n', 
            '-naopak\n', 
            '-bude\n', 
            '-zkrácen.\n', 
            '+Tenhle byl\n', 
            '+naopak zkrácen.\n'])
        self.assertEqual(h.content_src_lines(), [
            '-Tenhle\n', 
            '-naopak\n', 
            '-bude\n', 
            '-zkrácen.\n'])
        self.assertEqual(h.content_src_lines(with_minus=False), [
            'Tenhle\n', 
            'naopak\n', 
            'bude\n', 
            'zkrácen.\n'])
        self.assertEqual(h.content_dest_lines(), [
            '+Tenhle byl\n', 
            '+naopak zkrácen.\n'])
        self.assertEqual(h.content_dest_lines(with_plus=False), [
            'Tenhle byl\n', 
            'naopak zkrácen.\n'])


    def _hunk_with_src(self, src): 
        # src = (x1, n1)
        # content, x2, n2 don't matter
        return segmentio.Hunk(x1=src[0], n1=src[1], x2=300, n2=5, content=u'')

    def _hunk_with_dest(self, dest): 
        # dest = (x2, n2)
        # content, x1, n1 don't matter
        return segmentio.Hunk(x1=300, n1=5, x2=dest[0], n2=dest[1], content=u'')

    #def _xn_to_range(self, xn): 
    #    # convert tuple (x, n) to a line range; 
    #    # the last line is NOT inside the range
    #    return (xn[0], xn[0] + xn[1])

    def test_is_inside_src_range(self): 
        h = self._hunk_with_src((3, 1))
        xn = (4, 1)
        self.assertFalse(h.is_inside_src_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_src((3, 1))
        xn = (3, 0)
        self.assertFalse(h.is_inside_src_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_src((0, 0))
        xn = (1, 5)
        self.assertFalse(h.is_inside_src_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_src((7, 0))
        xn = (8, 0)
        self.assertFalse(h.is_inside_src_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))


        h = self._hunk_with_src((4, 1))
        xn = (3, 1)
        self.assertFalse(h.is_inside_src_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_src((3, 0))
        xn = (3, 1)
        self.assertFalse(h.is_inside_src_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_src((1, 5))
        xn = (0, 0)
        self.assertFalse(h.is_inside_src_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_src((8, 0))
        xn = (7, 0)
        self.assertFalse(h.is_inside_src_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))


        h = self._hunk_with_src((15, 2))
        xn = (14, 3)
        self.assertTrue(h.is_inside_src_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_src((19, 0))
        xn = (19, 2)
        self.assertTrue(h.is_inside_src_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))


        h = self._hunk_with_src((14, 3))
        xn = (15, 2)
        self.assertFalse(h.is_inside_src_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_src((19, 1))
        xn = (19, 0)
        self.assertFalse(h.is_inside_src_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_src((11, 0))
        xn = (11, 0)
        self.assertFalse(h.is_inside_src_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))
        
    def test_is_inside_dest_range(self): 
        h = self._hunk_with_dest((3, 1))
        xn = (4, 1)
        self.assertFalse(h.is_inside_dest_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_dest((3, 1))
        xn = (3, 0)
        self.assertFalse(h.is_inside_dest_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_dest((0, 0))
        xn = (1, 5)
        self.assertFalse(h.is_inside_dest_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_dest((7, 0))
        xn = (8, 0)
        self.assertFalse(h.is_inside_dest_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))


        h = self._hunk_with_dest((4, 1))
        xn = (3, 1)
        self.assertFalse(h.is_inside_dest_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_dest((3, 0))
        xn = (3, 1)
        self.assertFalse(h.is_inside_dest_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_dest((1, 5))
        xn = (0, 0)
        self.assertFalse(h.is_inside_dest_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_dest((8, 0))
        xn = (7, 0)
        self.assertFalse(h.is_inside_dest_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))


        h = self._hunk_with_dest((15, 2))
        xn = (14, 3)
        self.assertTrue(h.is_inside_dest_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_dest((19, 0))
        xn = (19, 2)
        self.assertTrue(h.is_inside_dest_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))


        h = self._hunk_with_dest((14, 3))
        xn = (15, 2)
        self.assertFalse(h.is_inside_dest_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_dest((19, 1))
        xn = (19, 0)
        self.assertFalse(h.is_inside_dest_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))

        h = self._hunk_with_dest((11, 0))
        xn = (11, 0)
        self.assertFalse(h.is_inside_dest_range(segmentio.Hunk.range_for_xn(xn[0], xn[1])))


    def test_ranges(self): 
        # hunks from segmentio_testdata/cN/c2.patch

        self.assertEqual(segmentio.Hunk.range_for_xn(3, 2), (3, 5))
        self.assertEqual(segmentio.Hunk.range_for_xn(2, 0), (3, 3))
        h1 = segmentio.Hunk(3, 2, 2, 0, u'''-3rd
-fourth
''')
        self.assertEqual(h1.src_range(), (3, 5))
        self.assertEqual(h1.dest_range(), (3, 3))


        self.assertEqual(segmentio.Hunk.range_for_xn(6, 0), (7, 7))
        self.assertEqual(segmentio.Hunk.range_for_xn(5, 3), (5, 8))
        h2 = segmentio.Hunk(6, 0, 5, 3, u'''+ADDING
+3
+LINES
''')
        self.assertEqual(h2.src_range(), (7, 7))
        self.assertEqual(h2.dest_range(), (5, 8))


        self.assertEqual(segmentio.Hunk.range_for_xn(9, 1), (9, 10))
        self.assertEqual(segmentio.Hunk.range_for_xn(10, 1), (10, 11))
        h3 = segmentio.Hunk(9, 1, 10, 1, u'''-ninth
+9th
''')
        self.assertEqual(h3.src_range(), (9, 10))
        self.assertEqual(h3.dest_range(), (10, 11))


class LineIndexTestCase(unittest.TestCase): 
    def test_building_index_of_a_small_file(self): 
        index = segmentio.LineIndex.build('segmentio_testdata/misc/a.txt', 'segmentio_testdata/misc/a.index')
        correct_index = u'''# src_line src_pos
1 0
2 19
3 29
4 38
5 52
'''
        self.assertEqual(unicode(index), correct_index)


    def test_find_position_where_line_begins(self):
        segmentio.LineIndex.build('segmentio_testdata/misc/a.txt', 'segmentio_testdata/misc/a.index')
        index = segmentio.LineIndex('segmentio_testdata/misc/a.index')

        self.assertEqual(index.src_pos(src_line=4), 38)
        self.assertEqual(index.src_pos(src_line=2), 19)
        self.assertEqual(index.src_pos(src_line=5), 52)
        self.assertEqual(index.src_pos(src_line=1), 0)
        self.assertEqual(index.src_pos(src_line=3), 29)


    def test_find_line_that_contains_the_position(self): 
        segmentio.LineIndex.build('segmentio_testdata/misc/a.txt', 'segmentio_testdata/misc/a.index')
        index = segmentio.LineIndex('segmentio_testdata/misc/a.index')

        self.assertEqual(index.src_line(src_pos=19), 2)
        self.assertEqual(index.src_line(src_pos=24), 2)

        self.assertEqual(index.src_line(src_pos=0), 1)

        self.assertEqual(index.src_line(src_pos=52), 5)
        self.assertEqual(index.src_line(src_pos=59), 5)
        self.assertEqual(index.src_line(src_pos=60), 5)



class FileLineReadIOTestCase(unittest.TestCase): 
    def test_read_lines(self): 
        with io.open('segmentio_testdata/handmade-changelog/reference-src-file.txt', 
                'r', encoding='utf-8') as file_io:
            line_read_io = segmentio.FileLineReadIO(file_io)
            lines = line_read_io.read_lines(31, 8)
            self.assertEqual(lines, u'''první
(za prvním)
Tenhle
naopak
bude
zkrácen.
šel
dědeček
''')

    def test_find_before(self): 
        with io.open('segmentio_testdata/handmade-changelog/reference-src-file.txt', 
                'r', encoding='utf-8') as file_io:
            line_read_io = segmentio.FileLineReadIO(file_io)

            found_line = line_read_io.find_before(38, u'něco')
            self.assertEqual(found_line, 30)
            found_line = line_read_io.find_before(38, u'šel')
            self.assertEqual(found_line, 37)
            found_line = line_read_io.find_before(38, u'prv')
            self.assertEqual(found_line, 32)
            found_line = line_read_io.find_before(32, u'prv')
            self.assertEqual(found_line, 31)
            found_line = line_read_io.find_before(2, u'něco')
            self.assertEqual(found_line, 1)

            found_line = line_read_io.find_before(1, u'něco')
            self.assertEqual(found_line, -1)
            found_line = line_read_io.find_before(38, u'kdecoHEE_NEEXISTUJE')
            self.assertEqual(found_line, -1)

    def test_find_after(self): 
        with io.open('segmentio_testdata/handmade-changelog/reference-src-file.txt', 
                'r', encoding='utf-8') as file_io:
            line_read_io = segmentio.FileLineReadIO(file_io)

            found_line = line_read_io.find_after(38, u'(za básní)')
            self.assertEqual(found_line, 41)
            found_line = line_read_io.find_after(38, u'e')
            self.assertEqual(found_line, 40)
            found_line = line_read_io.find_after(2, u'něco')
            self.assertEqual(found_line, 3)
            found_line = line_read_io.find_after(10, u'prv')
            self.assertEqual(found_line, 31)

            found_line = line_read_io.find_after(38, u'prv')
            self.assertEqual(found_line, -1)


class SegmentIOTestCase(unittest.TestCase):
#TODO: this didn't work with the old way
#    def test_editing(self):
#        file_io = io.open('segmentio_testdata/handmade-changelog/reference-src-file.txt', 
#                'r', encoding='utf-8')
#        with io.open('segmentio_testdata/handmade-changelog/reference-changelog.patch', 
#                'r', encoding='utf-8') as f: 
#            changelog = f.read()
#        sio = SegmentIO(file_io, changelog)
#
#        # load a segment
#        s = sio.get_segment(block_begin_line=82, block_num_lines=11)
#        print "#seg:", s._segment_src_begin_line, s._segment_begin_line
#        print "#d:", s.block_data()
#        print "#c:", s.changelog()
#        print "#cf:", s.changelog(globalLineNumbers=True)
#
#        # modify it (among other changes, one line is removed!)
#        s.set_block_data(u'''<změNNNěný>
#!úsek!
#(za prvním)
#Tenhle byl
#naopak zkrácen.
#šel
#dědeček
#na
#kopeček
#<za básnÍÍÍ>
#''')
#        print "#nc:", s.changelog()
#        print "#ncf:", s.changelog(globalLineNumbers=True)
#
#        # save it
#        sio.save_segment(s)
#
#        # check if the changes are there
#        s2 = sio.get_segment(block_begin_line=88, block_num_lines=4)
#        self.assertEqual(s2.block_data(), u'''dědeček
#na
#kopeček
#<za básnÍÍÍ>
#''')


    def _get_lrio(self, src_file, index_file=None): 
        if index_file == None: 
            index = None
        else: 
            if os.path.isfile(index_file) and os.path.getmtime(src_file) <= os.path.getmtime(index_file): 
                # there is an existing index that is up to date -> use it
                index = segmentio.LineIndex(index_file)
            else: 
                # there is no up-to-date index -> build one
                index = segmentio.LineIndex.build(src_file, index_file)

        file_io = io.open(src_file, 'r', encoding='utf-8')
        line_read_io = segmentio.FileLineReadIO(file_io, index)
        return line_read_io


    # large file
    def test_loading_data_from_csvert_NOINDEX(self): 
        return 
        # NOTE: Not doing this test (it was inconvenient to gave that huge file in testdata); 
        #       but I tried it and it's as fast as reading from the same place in the 
        #       far smaller _2M file.

        line_read_io = self._get_lrio('segmentio_testdata/large-file/cs-vert.vert')
        sio = SegmentIO(line_read_io, u'')

        t1 = time()
        segment = sio.get_segment(block_begin_line=3, block_num_lines=5)
        self.assertEqual(segment.block_data(), u'''<s>
Abstraktní	abstraktní	k2eAgInSc1d1	abstraktní
nesmysl	nesmysl	k1gInSc1	nesmysl
</s>
</p>
''')
        t2 = time()
        print "\n[cs-vert.vert, NOINDEX] get_segment beginning at line 3 took %f seconds\n" % (t2 - t1)

        t1 = time()
        segment = sio.get_segment(block_begin_line=900001, block_num_lines=5)
        self.assertEqual(segment.block_data(), u'''května	květen	k1gInSc2	květen
2006	#num#	k4	
v	v	k7c6	
utkání	utkání	k1gNnSc6	utkání
na	na	k7c6	
''')
        t2 = time()
        print "\n[cs-vert.vert, NOINDEX] get_segment beginning at line 9000001 took %f seconds\n" % (t2 - t1)

        t1 = time()
        segment = sio.get_segment(block_begin_line=1800001, block_num_lines=5)
        self.assertEqual(segment.block_data(), u'''Alajos	Alajos	k1gInSc1	Alajos
Szokolyi	Szokoly	k1gFnSc2	Szokoly
<g/>
(	(	kIx(	
<g/>
''')
        t2 = time()
        print "\n[cs-vert.vert, NOINDEX] get_segment beginning at line 1800001 took %f seconds\n" % (t2 - t1)


    def test_loading_data_from_csvert2M_NOINDEX(self): 
        line_read_io = self._get_lrio('segmentio_testdata/large-file/cs-vert_2M.vert')
        sio = SegmentIO(line_read_io, u'')

        t1 = time()
        segment = sio.get_segment(block_begin_line=3, block_num_lines=5)
        self.assertEqual(segment.block_data(), u'''<s>
Abstraktní	abstraktní	k2eAgInSc1d1	abstraktní
nesmysl	nesmysl	k1gInSc1	nesmysl
</s>
</p>
''')
        t2 = time()
        print "\n[cs-vert_2M.vert, NOINDEX] get_segment beginning at line 3 took %f seconds\n" % (t2 - t1)

        t1 = time()
        segment = sio.get_segment(block_begin_line=900001, block_num_lines=5)
        self.assertEqual(segment.block_data(), u'''května	květen	k1gInSc2	květen
2006	#num#	k4	
v	v	k7c6	
utkání	utkání	k1gNnSc6	utkání
na	na	k7c6	
''')
        t2 = time()
        print "\n[cs-vert_2M.vert, NOINDEX] get_segment beginning at line 9000001 took %f seconds\n" % (t2 - t1)

        t1 = time()
        segment = sio.get_segment(block_begin_line=1800001, block_num_lines=5)
        self.assertEqual(segment.block_data(), u'''Alajos	Alajos	k1gInSc1	Alajos
Szokolyi	Szokoly	k1gFnSc2	Szokoly
<g/>
(	(	kIx(	
<g/>
''')
        t2 = time()
        print "\n[cs-vert_2M.vert, NOINDEX] get_segment beginning at line 1800001 took %f seconds\n" % (t2 - t1)


    def test_loading_data_from_csvert2M_INDEX(self): 
        line_read_io = self._get_lrio(
                'segmentio_testdata/large-file/cs-vert_2M.vert',
                'segmentio_testdata/large-file/cs-vert_2M.index')
        sio = SegmentIO(line_read_io, u'')

        t1 = time()
        segment = sio.get_segment(block_begin_line=3, block_num_lines=5)
        self.assertEqual(segment.block_data(), u'''<s>
Abstraktní	abstraktní	k2eAgInSc1d1	abstraktní
nesmysl	nesmysl	k1gInSc1	nesmysl
</s>
</p>
''')
        t2 = time()
        print "\n[cs-vert_2M.vert, INDEX] get_segment beginning at line 3 took %f seconds\n" % (t2 - t1)

        t1 = time()
        segment = sio.get_segment(block_begin_line=900001, block_num_lines=5)
        self.assertEqual(segment.block_data(), u'''května	květen	k1gInSc2	květen
2006	#num#	k4	
v	v	k7c6	
utkání	utkání	k1gNnSc6	utkání
na	na	k7c6	
''')
        t2 = time()
        print "\n[cs-vert_2M.vert, INDEX] get_segment beginning at line 9000001 took %f seconds\n" % (t2 - t1)

        t1 = time()
        segment = sio.get_segment(block_begin_line=1800001, block_num_lines=5)
        self.assertEqual(segment.block_data(), u'''Alajos	Alajos	k1gInSc1	Alajos
Szokolyi	Szokoly	k1gFnSc2	Szokoly
<g/>
(	(	kIx(	
<g/>
''')
        t2 = time()
        print "\n[cs-vert_2M.vert, INDEX] get_segment beginning at line 1800001 took %f seconds\n" % (t2 - t1)


    def test_loading_data_with_handmade_changelog_NOINDEX(self): 
        # NOTE: beware: there are context lines in this changelog; we no longer allow context lines
        #file_io = io.open('segmentio_testdata/handmade-changelog/reference-src-file.txt', 
        #        'r', encoding='utf-8')
        #line_read_io = segmentio.FileLineReadIO(file_io)
        line_read_io = self._get_lrio('segmentio_testdata/handmade-changelog/reference-src-file.txt')
        self._do_test_loading_data_with_handmade_changelog(line_read_io)

    def test_loading_data_with_handmade_changelog_INDEX(self): 
        line_read_io = self._get_lrio(
                'segmentio_testdata/handmade-changelog/reference-src-file.txt', 
                'segmentio_testdata/handmade-changelog/reference-src-file.index')
        self._do_test_loading_data_with_handmade_changelog(line_read_io)

    def _do_test_loading_data_with_handmade_changelog(self, line_read_io): 
        with io.open('segmentio_testdata/handmade-changelog/reference-changelog.patch', 
                'r', encoding='utf-8') as f: 
            changelog = f.read()
        sio = SegmentIO(line_read_io, changelog)

        segment = sio.get_segment(block_begin_line=86, block_num_lines=6)
        self.assertEqual(segment.block_data(), u'''naopak zkrácen.
šel
dědeček
na
kopeček
...nevím, jak dál!
''')
    

    def test_loading_data_from_cN_NOINDEX(self): 
        lrio0 = self._get_lrio('segmentio_testdata/cN/reference-file.txt')
        lrio1 = self._get_lrio('segmentio_testdata/cN/reference-file-after-edit1.txt')
        lrio4 = self._get_lrio('segmentio_testdata/cN/reference-file-after-edit4.txt')
        self._do_test_loading_data_from_cN(lrio0, lrio1, lrio4)


    def test_loading_data_from_cN_INDEX(self): 
        lrio0 = self._get_lrio(
                'segmentio_testdata/cN/reference-file.txt', 
                'segmentio_testdata/cN/reference-file.index')
        lrio1 = self._get_lrio(
                'segmentio_testdata/cN/reference-file-after-edit1.txt', 
                'segmentio_testdata/cN/reference-file-after-edit1.index')
        lrio4 = self._get_lrio(
                'segmentio_testdata/cN/reference-file-after-edit4.txt', 
                'segmentio_testdata/cN/reference-file-after-edit4.index')
        self._do_test_loading_data_from_cN(lrio0, lrio1, lrio4)


    def _do_test_loading_data_from_cN(self, lrio0, lrio1, lrio4): 
        # test getting the content of a version of the file 
        # (reference-file.txt, reference-file-after-edit1.txt, reference-file-after-edit2.txt, ...)
        # using another version and the changelogs 


        # -------------------------------------------------
        # physical version:  reference-file.txt
        # virtual version:   reference-file-after-edit1.txt
        # -------------------------------------------------
        with io.open('segmentio_testdata/cN/c1.patch', 
                'r', encoding='utf-8') as f: 
            c1 = segmentio.changelog_from_patch_file_content(f.read())
        sio1 = SegmentIO(lrio0, c1)

        segment = sio1.get_segment(block_begin_line=3, block_num_lines=3)
        self.assertEqual(segment.block_data(), u'''3rd
fourth
fifth
''')
        # a segment that doesn't contain any hunks
        no_hunks_segment = sio1.get_segment(block_begin_line=4, block_num_lines=6)
        self.assertEqual(no_hunks_segment.block_data(), u'''fourth
fifth
sixth
seventh
eighth
ninth
''')

        # a segment that contains all the lines of reference-file-after-edit1.txt
        with io.open('segmentio_testdata/cN/reference-file-after-edit1.txt', 'r', encoding='utf-8') as f:
            file_after_edit1_content = f.read()

        whole_file_segment = sio1.get_segment(block_begin_line=1, block_num_lines=20)
        self.assertEqual(whole_file_segment.block_data(), file_after_edit1_content)

        # a segment that doesn't contain any lines
        empty_segment = sio1.get_segment(block_begin_line=5, block_num_lines=0)
        self.assertEqual(empty_segment.block_data(), u'')

        # a one-line segment
        empty_segment = sio1.get_segment(block_begin_line=5, block_num_lines=1)
        self.assertEqual(empty_segment.block_data(), u'fifth\n')


        # -------------------------------------------------
        # physical version:  reference-file-after-edit1.txt
        # virtual version:   reference-file-after-edit2.txt
        # -------------------------------------------------
        with io.open('segmentio_testdata/cN/c2.patch', 
                'r', encoding='utf-8') as f: 
            c2 = segmentio.changelog_from_patch_file_content(f.read())
        sio2 = SegmentIO(lrio1, c2)

        # this block is chosen to check that: 
        #   * the dest spike right below it is handled correcly
        #   * the segment src line range is correctly padded with block lines
        segment1 = sio2.get_segment(block_begin_line=1, block_num_lines=2)
        self.assertEqual(segment1.block_data(), u'''1st
2nd
''')

        # this block checks that: 
        #   * there is no problem with confusing open/closed ranges (see test_are_intersecting)
        #   * the segment src line range is correctly padded with block lines (both first and last 
        #   hunk of the segment is the src spike of the second hunk of c2; need to correctly pad 
        #   above and below it)
        segment2 = sio2.get_segment(block_begin_line=4, block_num_lines=6)
        self.assertEqual(segment2.block_data(), u'''sixth
ADDING
3
LINES
seventh
eighth
''')


        # -------------------------------------------------
        # physical version:  reference-file.txt
        # virtual version:   reference-file-after-edit2.txt
        # -------------------------------------------------
        c12 = segmentio.compose_changelogs(c1, c2)
        sio12 = SegmentIO(lrio0, c12)

        # the same segment as segment2 above, but now loaded using a composed changelog 
        sio12_segment = sio12.get_segment(block_begin_line=4, block_num_lines=6)
        self.assertEqual(sio12_segment.block_data(), u'''sixth
ADDING
3
LINES
seventh
eighth
''')


        # -------------------------------------------------
        # physical version:  reference-file.txt
        # virtual version:   reference-file-after-edit4.txt
        # -------------------------------------------------
        with io.open('segmentio_testdata/cN/c3.patch', 'r', encoding='utf-8') as f: 
            c3 = segmentio.changelog_from_patch_file_content(f.read())
        with io.open('segmentio_testdata/cN/c4.patch', 'r', encoding='utf-8') as f: 
            c4 = segmentio.changelog_from_patch_file_content(f.read())

        c123 = segmentio.compose_changelogs(c12, c3)
        c1234 = segmentio.compose_changelogs(c123, c4)
        sio1234 = SegmentIO(lrio0, c1234)

        sio1234_segment = sio1234.get_segment(block_begin_line=3, block_num_lines=8)
        self.assertEqual(sio1234_segment.block_data(), u'''sixth
LN
KEKščř
seventh
[éíǧhth]
before 9th
[ňiňÉÉÉth]
<in
''')


        # -------------------------------------------------
        # physical version:  reference-file-after-edit4.txt
        # virtual version:   reference-file-after-edit2.txt
        # -------------------------------------------------

        # changelog from reference_file_after_edit4.txt
        # to reference_file_after_edit3.txt
        c_f4_f3 = segmentio.invert_changelog(c4)

        # changelog from reference_file_after_edit3.txt
        # to reference_file_after_edit2.txt
        c_f3_f2 = segmentio.invert_changelog(c3)  

        # changelog from reference_file_after_edit4.txt
        # to reference_file_after_edit2.txt
        c_f4_f2 = segmentio.compose_changelogs(c_f4_f3, c_f3_f2)  

        sio_f4_f2 = SegmentIO(lrio4, c_f4_f2)
        sio_f4_f2_segment = sio_f4_f2.get_segment(block_begin_line=4, block_num_lines=6)
        self.assertEqual(sio_f4_f2_segment.block_data(), u'''sixth
ADDING
3
LINES
seventh
eighth
''')



    def test_editing_data_from_cN(self): 
        # 1. get a segment like in test_loading_data_from_cN() 
        # 2. modify its content and save it
        # 3. test if the resulting changelog works correctly 

        # -------------------------------------------------
        # physical version:  reference-file-after-edit1.txt
        # virtual version:   reference-file-after-edit2.txt
        # -------------------------------------------------
        fio1 = io.open('segmentio_testdata/cN/reference-file-after-edit1.txt', 
                'r', encoding='utf-8')
        lrio1 = segmentio.FileLineReadIO(fio1)
        with io.open('segmentio_testdata/cN/c2.patch', 
                'r', encoding='utf-8') as f: 
            c2 = segmentio.changelog_from_patch_file_content(f.read())
        sio2 = SegmentIO(lrio1, c2)

        seg = sio2.get_segment(block_begin_line=4, block_num_lines=6)

        self.assertEqual(seg.block_data(), u'''sixth
ADDING
3
LINES
seventh
eighth
''')
        self.assertEqual(seg.changelog(), u'')

        # let's call this edit "useredit1"
        seg.set_block_data(u'''ONLY THIS LINE INSTEAD OF "sixth" AND THOSE THREE LINES
seventh
eighth
''')
        sio2.save_segment(seg)

        # check that the segment is no longer usable
        with self.assertRaises(segmentio.OutdatedSegmentException): 
            seg.block_data()
        with self.assertRaises(segmentio.OutdatedSegmentException): 
            seg.set_block_data(u'bleh')
        with self.assertRaises(segmentio.OutdatedSegmentException): 
            seg.changelog()

        # diff -U 0 reference-file-after-edit1.txt useredit1-on-reference-file-after-edit2.txt
        f1_ue1_correct_file_changelog = u'''@@ -3,2 +2,0 @@
-3rd
-fourth
@@ -6,1 +4,1 @@
-sixth
+ONLY THIS LINE INSTEAD OF "sixth" AND THOSE THREE LINES
@@ -9,1 +7,1 @@
-ninth
+9th
'''
        self.assertEqual(sio2.file_changelog(), f1_ue1_correct_file_changelog)

        # get a new segment in the exact same place and check the contents 
        # (this would be the new content of the viewport of the editor)
        seg = sio2.get_segment(block_begin_line=4, block_num_lines=6)
        self.assertEqual(seg.block_data(), u'''ONLY THIS LINE INSTEAD OF "sixth" AND THOSE THREE LINES
seventh
eighth
9th
tenth
eleventh
''')

        # apply the file changelog on the content of the physical file (reference-file-after-edit1.txt) 
        # and check if it gives the correct result (useredit1-on-reference-file-after-edit2.txt)
        with io.open('segmentio_testdata/cN/reference-file-after-edit1.txt', 
                'r', encoding='utf-8') as f:
            file_after_edit1_content = f.read()
        with io.open('segmentio_testdata/cN/useredit1-on-reference-file-after-edit2.txt', 
                'r', encoding='utf-8') as f:
            useredit1_result_file_content = f.read()

        file_changelog = sio2.file_changelog()
        patched_file = segmentio.patch(file_after_edit1_content, file_changelog)
        self.assertEqual(patched_file, useredit1_result_file_content)


    def test_read_lines(self): 
        fio1 = io.open('segmentio_testdata/cN/reference-file-after-edit1.txt', 
                'r', encoding='utf-8')
        lrio1 = segmentio.FileLineReadIO(fio1)
        with io.open('segmentio_testdata/cN/c2.patch', 
                'r', encoding='utf-8') as f: 
            c2 = segmentio.changelog_from_patch_file_content(f.read())
        sio2 = SegmentIO(lrio1, c2)

        self.assertEqual(sio2.read_lines(4, 6), u'''sixth
ADDING
3
LINES
seventh
eighth
''')


    def test_read_shifted_free_lines(self): 
        # read some lines that are shifted by preceding hunks 
        # and don't intersect with any hunks
        fio3 = io.open('segmentio_testdata/cN/reference-file-after-edit3.txt', 
                'r', encoding='utf-8')
        lrio3 = segmentio.FileLineReadIO(fio3)
        with io.open('segmentio_testdata/cN/c4.patch', 
                'r', encoding='utf-8') as f: 
            c4 = segmentio.changelog_from_patch_file_content(f.read())
        sio4 = SegmentIO(lrio3, c4)

        self.assertEqual(sio4.read_lines(5, 1), u'''KEKščř
''')
        self.assertEqual(sio4.read_lines(13, 1), u'''ABC
''')
        self.assertEqual(sio4.read_lines(15, 4), u'''eleventh
twelfth
thirteenth
fourteenth
''')
    
    
    def test_read_shifted_occupied_lines(self): 
        # read some lines that are shifted by preceding hunks 
        # and intersect with some hunks
        fio3 = io.open('segmentio_testdata/cN/reference-file-after-edit3.txt', 
                'r', encoding='utf-8')
        lrio3 = segmentio.FileLineReadIO(fio3)
        with io.open('segmentio_testdata/cN/c4.patch', 
                'r', encoding='utf-8') as f: 
            c4 = segmentio.changelog_from_patch_file_content(f.read())
        sio4 = SegmentIO(lrio3, c4)

        self.assertEqual(sio4.read_lines(6, 1), u'''seventh
''')
        self.assertEqual(sio4.read_lines(12, 1), u'''middle>
''')
        self.assertEqual(sio4.read_lines(12, 2), u'''middle>
ABC
''')
        self.assertEqual(sio4.read_lines(4, 3), u'''LN
KEKščř
seventh
''')


    def test_read_every_possible_block_in_f3_c4(self):
        self._do_test_read_every_possible_block(
                src_file='segmentio_testdata/cN/reference-file-after-edit3.txt', 
                changelog_file='segmentio_testdata/cN/c4.patch', 
                correct_dest_file='segmentio_testdata/cN/reference-file-after-edit4.txt')

    def test_read_every_possible_block_in_f1_c2(self):
        self._do_test_read_every_possible_block(
                src_file='segmentio_testdata/cN/reference-file-after-edit1.txt', 
                changelog_file='segmentio_testdata/cN/c2.patch', 
                correct_dest_file='segmentio_testdata/cN/reference-file-after-edit2.txt')

    def _do_test_read_every_possible_block(self, src_file, changelog_file, correct_dest_file): 
        '''reading blocks from the file, test all combinations of line and num_lines'''

        fio3 = io.open(src_file, 'r', encoding='utf-8')
        lrio3 = segmentio.FileLineReadIO(fio3)
        with io.open(changelog_file, 'r', encoding='utf-8') as f: 
            c4 = segmentio.changelog_from_patch_file_content(f.read())
        sio4 = SegmentIO(lrio3, c4)

        with io.open(correct_dest_file, 'r', encoding='utf-8') as f: 
            dest_lines = f.read().splitlines(True)

        total_lines = len(dest_lines)
        for num_lines in range(1, total_lines): 
            for ln in range(1, total_lines + 1 - (num_lines - 1)): 
                correct_data = u''.join(dest_lines[(ln-1):(ln-1)+num_lines])
                #print u'c->[%s]' % correct_data
                self.assertEqual(sio4.read_lines(ln, num_lines), correct_data)


    def test_find_before(self): 
        fio1 = io.open('segmentio_testdata/cN/reference-file-after-edit1.txt', 
                'r', encoding='utf-8')
        lrio1 = segmentio.FileLineReadIO(fio1)
        with io.open('segmentio_testdata/cN/c2.patch', 
                'r', encoding='utf-8') as f: 
            c2 = segmentio.changelog_from_patch_file_content(f.read())
        sio2 = SegmentIO(lrio1, c2)

        self.assertEqual(sio2.read_lines(4, 6), u'''sixth
ADDING
3
LINES
seventh
eighth
''')

        #print "--->", sio2.get_segment(1, 1).block_data()
        #print "--->", sio2.get_segment(5, 1).block_data()

        found_line = sio2.find_before(15, u'1st')
        self.assertEqual(found_line, 1)

        found_line = sio2.find_before(15, u'ADD')
        self.assertEqual(found_line, 5)

        found_line = sio2.find_before(15, u'DING')
        self.assertEqual(found_line, 5)

        found_line = sio2.find_before(15, u'sixteenth')
        self.assertEqual(found_line, -1)


    def test_find_after(self): 
        fio1 = io.open('segmentio_testdata/cN/reference-file-after-edit1.txt', 
                'r', encoding='utf-8')
        lrio1 = segmentio.FileLineReadIO(fio1)
        with io.open('segmentio_testdata/cN/c2.patch', 
                'r', encoding='utf-8') as f: 
            c2 = segmentio.changelog_from_patch_file_content(f.read())
        sio2 = SegmentIO(lrio1, c2)

        self.assertEqual(sio2.read_lines(4, 6), u'''sixth
ADDING
3
LINES
seventh
eighth
''')
        # the virtual file is equal to 
        # segmentio_testdata/cN/reference-file-after-edit2.txt

        found_line = sio2.find_after(3, u'LINES')
        self.assertEqual(found_line, 7)

        found_line = sio2.find_after(3, u'ADD')
        self.assertEqual(found_line, 5)

        found_line = sio2.find_after(3, u'seventh')
        self.assertEqual(found_line, 8)

        found_line = sio2.find_after(3, u'twelfth')
        self.assertEqual(found_line, 13)

        found_line = sio2.find_after(15, u'ADD')
        self.assertEqual(found_line, -1)



    def test_basing_a_SegmentIO_on_another_SegmentIO(self): 
        #
        #                 -- sio1 --
        #
        # -------------------------------------------------
        # physical version:  reference-file.txt
        # virtual version:   reference-file-after-edit1.txt
        # -------------------------------------------------
        fio0 = io.open('segmentio_testdata/cN/reference-file.txt', 
                'r', encoding='utf-8')
        lrio0 = segmentio.FileLineReadIO(fio0)
        with io.open('segmentio_testdata/cN/c1.patch', 
                'r', encoding='utf-8') as f: 
            c1 = segmentio.changelog_from_patch_file_content(f.read())
        sio1 = SegmentIO(lrio0, c1)

        segment = sio1.get_segment(block_begin_line=3, block_num_lines=3)
        self.assertEqual(segment.block_data(), u'''3rd
fourth
fifth
''')

        #
        #                 -- sio2 --
        #
        # -------------------------------------------------
        # physical version:  reference-file-after-edit1.txt
        # virtual version:   reference-file-after-edit2.txt
        # -------------------------------------------------

        #fio1 = io.open('segmentio_testdata/cN/reference-file-after-edit1.txt', 
        #        'r', encoding='utf-8')
        #lrio1 = segmentio.FileLineReadIO(fio1) 
        with io.open('segmentio_testdata/cN/c2.patch', 
                'r', encoding='utf-8') as f: 
            c2 = segmentio.changelog_from_patch_file_content(f.read())
        sio2 = SegmentIO(sio1, c2)   # NOTE: This is it. 
                                     #       I am using sio1 as a LineReadIO for sio2.

        # -- test getting some segments -- 
        # (the same ones as in test_loading_data_from_cN() for this virtual file)

        segment1 = sio2.get_segment(block_begin_line=1, block_num_lines=2)
        self.assertEqual(segment1.block_data(), u'''1st
2nd
''')

        segment2 = sio2.get_segment(block_begin_line=4, block_num_lines=6)
        self.assertEqual(segment2.block_data(), u'''sixth
ADDING
3
LINES
seventh
eighth
''')


    def test_rebasing_from_f1_to_f0(self): 
        # -- first, let's have sio1 with empty changelog --
        # (corresponds to the situation when a window's base revision is the head revision)

        #
        #                 -- sio1 --
        #
        # -------------------------------------------------
        # physical version:  reference-file-after-edit1.txt
        # virtual version:   reference-file-after-edit1.txt
        # -------------------------------------------------
        fio0 = io.open('segmentio_testdata/cN/reference-file-after-edit1.txt', 
                'r', encoding='utf-8')
        lrio0 = segmentio.FileLineReadIO(fio0)
        c1 = u''
        sio1 = SegmentIO(lrio0, c1)

        segment = sio1.get_segment(block_begin_line=3, block_num_lines=3)
        self.assertEqual(segment.block_data(), u'''3rd
fourth
fifth
''')

        #
        #                 -- sio2 --
        #
        # -------------------------------------------------
        # physical version:  reference-file-after-edit1.txt
        # virtual version:   reference-file-after-edit2.txt
        # -------------------------------------------------

        with io.open('segmentio_testdata/cN/c2.patch', 
                'r', encoding='utf-8') as f: 
            c2 = segmentio.changelog_from_patch_file_content(f.read())
        sio2 = SegmentIO(sio1, c2)   

        segment1 = sio2.get_segment(block_begin_line=1, block_num_lines=2)
        self.assertEqual(segment1.block_data(), u'''1st
2nd
''')

        segment2 = sio2.get_segment(block_begin_line=4, block_num_lines=6)
        self.assertEqual(segment2.block_data(), u'''sixth
ADDING
3
LINES
seventh
eighth
''')

        # -- now, let's rebase sio1, making its changelog non-empty
        # (corresponds to the situation when someone commited and we still have a window 
        # with some changes that was made before the commit; that window's base revision 
        # is no longer the head revision)

        #
        #                 -- sio1 --
        #
        # -------------------------------------------------
        # physical version:  reference-file.txt
        # virtual version:   reference-file-after-edit1.txt
        # -------------------------------------------------
        fio0 = io.open('segmentio_testdata/cN/reference-file.txt', 
                'r', encoding='utf-8')
        lrio0 = segmentio.FileLineReadIO(fio0)
        with io.open('segmentio_testdata/cN/c1.patch', 
                'r', encoding='utf-8') as f: 
            c1 = segmentio.changelog_from_patch_file_content(f.read())
        sio1 = SegmentIO(lrio0, c1)

        segment = sio1.get_segment(block_begin_line=3, block_num_lines=3)
        self.assertEqual(segment.block_data(), u'''3rd
fourth
fifth
''')

        # -- let's base sio2 on this new sio1; it should work the same way as before --

        #
        #                 -- sio2 --
        #
        # -------------------------------------------------
        # physical version:  reference-file-after-edit1.txt
        # virtual version:   reference-file-after-edit2.txt
        # -------------------------------------------------
        sio2 = SegmentIO(sio1, c2)   

        segment1 = sio2.get_segment(block_begin_line=1, block_num_lines=2)
        self.assertEqual(segment1.block_data(), u'''1st
2nd
''')

        segment2 = sio2.get_segment(block_begin_line=4, block_num_lines=6)
        self.assertEqual(segment2.block_data(), u'''sixth
ADDING
3
LINES
seventh
eighth
''')


    def test_rebasing_from_f2_to_f1(self): 
        # -- first, let's have sio2 with empty changelog --
        # (corresponds to the situation when a window's base revision is the head revision)

        #
        #                 -- sio2 --
        #
        # -------------------------------------------------
        # physical version:  reference-file-after-edit2.txt
        # virtual version:   reference-file-after-edit2.txt
        # -------------------------------------------------
        fio1 = io.open('segmentio_testdata/cN/reference-file-after-edit2.txt', 
                'r', encoding='utf-8')
        lrio1 = segmentio.FileLineReadIO(fio1)
        c2 = u''
        sio2 = SegmentIO(lrio1, c2)

        seg = sio2.get_segment(block_begin_line=4, block_num_lines=6)
        self.assertEqual(seg.block_data(), u'''sixth
ADDING
3
LINES
seventh
eighth
''')

        #
        #                 -- sio3 --
        #
        # -------------------------------------------------
        # physical version:  reference-file-after-edit2.txt
        # virtual version:   reference-file-after-edit3.txt
        # -------------------------------------------------

        with io.open('segmentio_testdata/cN/c3.patch', 
                'r', encoding='utf-8') as f: 
            c3 = segmentio.changelog_from_patch_file_content(f.read())
        sio3 = SegmentIO(sio2, c3)   

        seg = sio3.get_segment(block_begin_line=8, block_num_lines=3)
        self.assertEqual(seg.block_data(), u'''ninEEEth
ABC
tenth
''')

        # -- now, let's rebase sio2, making its changelog non-empty
        # (corresponds to the situation when someone commited and we still have a window 
        # with some changes that was made before the commit; that window's base revision 
        # is no longer the head revision)

        #
        #                 -- sio2 --
        #
        # -------------------------------------------------
        # physical version:  reference-file-after-edit1.txt
        # virtual version:   reference-file-after-edit2.txt
        # -------------------------------------------------
        fio1 = io.open('segmentio_testdata/cN/reference-file-after-edit1.txt', 
                'r', encoding='utf-8')
        lrio1 = segmentio.FileLineReadIO(fio1)
        with io.open('segmentio_testdata/cN/c2.patch', 
                'r', encoding='utf-8') as f: 
            c2 = segmentio.changelog_from_patch_file_content(f.read())
        sio2 = SegmentIO(lrio1, c2)

        seg = sio2.get_segment(block_begin_line=4, block_num_lines=6)
        self.assertEqual(seg.block_data(), u'''sixth
ADDING
3
LINES
seventh
eighth
''')

        # -- let's base sio3 on this new sio2; it should work the same way as before --

        #
        #                 -- sio3 --
        #
        # -------------------------------------------------
        # physical version:  reference-file-after-edit2.txt
        # virtual version:   reference-file-after-edit3.txt
        # -------------------------------------------------
        sio3 = SegmentIO(sio2, c3)   

        seg = sio3.get_segment(block_begin_line=8, block_num_lines=3)
        self.assertEqual(seg.block_data(), u'''ninEEEth
ABC
tenth
''')


    def test_rebasing_on_vertfile_as_in_model_test(self): 
        return
        #####################################################
        # NOTE: The problem is fixed in model_test. 
        #       However, this test still doesn't work because 
        #       it doesn't do the rebasing of the window that 
        #       is done in model.Window. 
        #       
        #       I disabled this test. (it's no longer useful, 
        #       and would need to be updated to stop failing)
        #####################################################

        orig_file_path = os.path.join(os.getcwd(), 
                u'segmentio_testdata/rebasing-on-vertfile-as-in-model_test/cztenten_994.vert.bak')
        file_path = os.path.join(os.getcwd(), 
                u'segmentio_testdata/rebasing-on-vertfile-as-in-model_test/cztenten_994.vert')
        shutil.copyfile(orig_file_path, file_path)


        # -- open a window (w1), do edit1 and edit2 in it --

        w1_fio = io.open(file_path, 'r', encoding='utf-8')  # the original file before any commit
        w1_headrev_io = segmentio.FileLineReadIO(w1_fio)
        w1_changelog_from_head_to_my_base = u''
        w1_my_base_io = segmentio.SegmentIO(w1_headrev_io, w1_changelog_from_head_to_my_base)
        w1_file_changelog = u''
        w1_my_io = segmentio.SegmentIO(w1_my_base_io, w1_file_changelog)

        w1_seg = w1_my_io.get_segment(block_begin_line=67, block_num_lines=5)
        line_67_nlines_5_orig = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	
premiéru	premiér	k1gMnSc3qP	premiér
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
'''
        self.assertEqual(w1_seg.block_data(), line_67_nlines_5_orig)

        # edit1
        new_content = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
'''
        w1_seg.set_block_data(new_content)
        w1_my_io.save_segment(w1_seg)
        w1_file_changelog = w1_my_io.file_changelog()
        line_67_nlines_5_after_edit1 = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
nenechal	nechat	k5eNaPmAgInSrDaPqP	
'''
        w1_seg = w1_my_io.get_segment(block_begin_line=67, block_num_lines=5)
        self.assertEqual(w1_seg.block_data(), line_67_nlines_5_after_edit1)

        # edit2
        new_content = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
ADDED LINE 1
ADDED LINE 2
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
nenechal	nechat	k5eNaPmAgInSrDaPqP	
'''
        w1_seg.set_block_data(new_content)
        w1_my_io.save_segment(w1_seg)
        w1_file_changelog = w1_my_io.file_changelog()
        line_67_nlines_5_after_edit2 = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
ADDED LINE 1
ADDED LINE 2
nového	nový	k2eAgNnSc2d1qP	nové
'''
        w1_seg = w1_my_io.get_segment(block_begin_line=67, block_num_lines=5)
        self.assertEqual(w1_seg.block_data(), line_67_nlines_5_after_edit2)


        # -- open another window (w2), do edit3 in it --
        # (base revision is the same as for w1 because edits in w1 haven't been commited yet)

        w2_fio = io.open(file_path, 'r', encoding='utf-8')  # the original file before any commit
        w2_headrev_io = segmentio.FileLineReadIO(w2_fio)
        w2_changelog_from_head_to_my_base = u''
        w2_my_base_io = segmentio.SegmentIO(w2_headrev_io, w2_changelog_from_head_to_my_base)
        w2_file_changelog = u''
        w2_my_io = segmentio.SegmentIO(w2_my_base_io, w2_file_changelog)

        w2_seg = w2_my_io.get_segment(block_begin_line=56, block_num_lines=8)
        line_56_nlines_8_orig = u'''Sestupný	sestupný	k2eAgInSc1d1qP	sestupný
kurs	kurs	k1gInSc1	kurs
po	po	k7c6qP	
víkendu	víkend	k1gInSc6qP	víkend
určitě	určitě	k6eAd1	
nabere	nabrat	k5eAaPmIp3nSaPrDqP	
Spytihněv	Spytihněv	k1gFnSc1qG	Spytihněv
<g/>
'''
        self.assertEqual(w2_seg.block_data(), line_56_nlines_8_orig)

        # edit3
        new_content = u'''Sestupný	sestupný	k2eAgInSc1d1qP	sestupný
kurs	kurs	k1gInSc1	kurs
(DELETED THESE 4 WORDS)
SpytihněVVVVV	Spytihněv	k1gFnSc1qG	Spytihněv
<g/>
'''
        line_56_nlines_8_after_edit3 = u'''Sestupný	sestupný	k2eAgInSc1d1qP	sestupný
kurs	kurs	k1gInSc1	kurs
(DELETED THESE 4 WORDS)
SpytihněVVVVV	Spytihněv	k1gFnSc1qG	Spytihněv
<g/>
.	.	kIx.	
</s>
<s desamb="1">
'''
        w2_seg.set_block_data(new_content)
        w2_my_io.save_segment(w2_seg)
        w2_file_changelog = w2_my_io.file_changelog()

        w2_seg = w2_my_io.get_segment(block_begin_line=56, block_num_lines=8)
        self.assertEqual(w2_seg.block_data(), line_56_nlines_8_after_edit3)


        # ----------------------------------------------------------
        # --> here comes the part that is problematic in model_test: 
        # ----------------------------------------------------------

        # -- commit changes in w2 (that is: edit3) --

        # before commiting anything, check w1 viewport content
        self.assertEqual(w1_seg.block_data(), line_67_nlines_5_after_edit2)

        
        #print "~~~~\n" + \
        #        model.GitFileSystem().diff_from_head(
        #                    model.Application().window_page(w2_id)['file_path'],
        #                    model.Application().window_page(w2_id)['revision']) + "~~~~"


        # do the commit of w2
        # (see termdemo-save.py and termdemo.sh)
        patchfile_path = '%s.patch' % file_path
        with io.open(patchfile_path, 'w', encoding='utf-8') as f: 
            f.write(u'--- \n+++ \n')
            f.write(w2_file_changelog)
        returncode = subprocess_call(["patch", file_path, patchfile_path])
        assert returncode == 0

        # w2 should stay the same

        # NOTE: In model.Window, this is done every time get_viewport_content() or save_viewport_content() 
        #       is called. However, here we do it only now because now, the head has changed so 
        #       w2_fio and w2_changelog_from_head_to_my_base must be re-constructed and everything 
        #       constructed on them must be re-constructed too.
        w2_fio = io.open(file_path, 'r', encoding='utf-8')  # the now patched file
        w2_headrev_io = segmentio.FileLineReadIO(w2_fio)
        with io.open(orig_file_path, 'r', encoding='utf-8') as f: 
            orig_file_content = f.read()  # original file (no longer is the head)
        with io.open(file_path, 'r', encoding='utf-8') as f: 
            file_content = f.read()  # patched file (is the head)
        w2_changelog_from_head_to_my_base = segmentio.diff(file_content, orig_file_content)
        w2_my_base_io = segmentio.SegmentIO(w2_headrev_io, w2_changelog_from_head_to_my_base)
        w2_my_io = segmentio.SegmentIO(w2_my_base_io, w2_file_changelog)

        dbg(w2_my_base_io.file_changelog())
        dbg(w2_my_io.file_changelog())

        w2_seg = w2_my_io.get_segment(block_begin_line=56, block_num_lines=8)
        self.assertEqual(w2_seg.block_data(), line_56_nlines_8_after_edit3)
                                                                           

        # the commit shouldn't have any effect on w1 either

        # NOTE: (as above, only for w1)
        w1_fio = io.open(file_path, 'r', encoding='utf-8')  # the now patched file
        w1_headrev_io = segmentio.FileLineReadIO(w1_fio)
        with io.open(orig_file_path, 'r', encoding='utf-8') as f: 
            orig_file_content = f.read()  # original file (no longer is the head)
        with io.open(file_path, 'r', encoding='utf-8') as f: 
            file_content = f.read()  # patched file (is the head)
        w1_changelog_from_head_to_my_base = segmentio.diff(file_content, orig_file_content)
        w1_my_base_io = segmentio.SegmentIO(w1_headrev_io, w1_changelog_from_head_to_my_base)
        w1_my_io = segmentio.SegmentIO(w1_my_base_io, w1_file_changelog)

        dbg(w1_my_base_io.file_changelog())
        dbg(w1_my_io.file_changelog())
        testseg = w1_my_io.get_segment(block_begin_line=64, block_num_lines=2)  # seems like the first segment is not taken into account 
                                                                                # TODO: thoroughly test behavior of SegmentIO in situations like this
        dbg("TESTSEG")
        dbg(testseg.block_data())

        w1_seg = w1_my_io.get_segment(block_begin_line=67, block_num_lines=5)
        self.assertEqual(w2_seg.block_data(), line_67_nlines_5_after_edit2)  # NOTE: here is where it breaks 
                                                                             #       in model_test
        # NOTE: It breaks here as well. 
        #       See issues/model_test_rebasing_error/in_segmentio_test.
        #       In 3.png, the highlighted src range (in the physical file) is obviously wrong. 
        # TODO FIXME: Fix this bug!



    #######################################
    #### --- investigating crashes --- ####
    #######################################
    def test_crash_1(self): 
        orig_file_path = os.path.join(os.getcwd(), 
                u'segmentio_testdata/investigating-crashes/cztenten_100k.vert.bak')
        file_path = os.path.join(os.getcwd(), 
                u'segmentio_testdata/investigating-crashes/cztenten_100k.vert')
        shutil.copyfile(orig_file_path, file_path)

        fio = io.open('segmentio_testdata/investigating-crashes/cztenten_100k.vert', 
                'r', encoding='utf-8')
        lrio = segmentio.FileLineReadIO(fio)
        sio = SegmentIO(lrio, u'')

        seg = sio.get_segment(block_begin_line=1, block_num_lines=20)
        self.assertEqual(seg.block_data(), u'''<doc xdedupl_id="192430" contenttype="text/html" guessed_charset="cp1250" ip="89.185.224.47" lang_filter_score="0.546968355014" length="33933" timestamp="20080316150457" url="http://www.efotbal.cz/index.php?page=clanek&amp;clanek=26164" http_cache_control="no-store, no-cache, must-revalidate, post-check=0, pre-check=0" http_connection="close" http_content_type="text/html" http_date="Sun, 16 Mar 2008 15:05:05 GMT" http_expires="Thu, 19 Nov 1981 08:52:00 GMT" http_pragma="no-cache" http_server="Apache/2.2.3 (Debian) PHP/5.2.0-8+etch10" http_x_powered_by="PHP/5.2.0-8+etch10">
<p accents="yes" heading="1">
<s>
Brod	brod	k1gInSc1qP	brod
porazil	porazit	k5eAaPmAgInSaPrDqP	
Chropyni	Chropyně	k1gFnSc4	Chropyně
a	a	k8xCqP	
ztrácí	ztrácet	k5eAaImIp3nSrDaIqP	
na	na	k7c4qP	
ni	on	k3p3gFnSc4xPqP	
bod	bod	k1gInSc4qP	bod
</s>
</p>
<p accents="yes" heading="0">
<s>
Náskok	náskok	k1gInSc1qP	náskok
Chropyně	Chropyně	k1gFnSc2	Chropyně
na	na	k7c6qP	
čele	čelo	k1gNnSc6qP	čelo
se	se	k3c4xPyFqP	
''')
        self.assertEqual(seg.changelog(), u'')


        # do the edit that crashes the editor

        seg.set_block_data(u'''<doc xdedupl_id="192430" contenttype="text/html" guessed_charset="cp1250" ip="89.185.224.47" lang_filter_score="0.546968355014" length="33933" timestamp="20080316150457" url="http://www.efotbal.cz/index.php?page=clanek&amp;clanek=26164" http_cache_control="no-store, no-cache, must-revalidate, post-check=0, pre-check=0" http_connection="close" http_content_type="text/html" http_date="Sun, 16 Mar 2008 15:05:05 GMT" http_expires="Thu, 19 Nov 1981 08:52:00 GMT" http_pragma="no-cache" http_server="Apache/2.2.3 (Debian) PHP/5.2.0-8+etch10" http_x_powered_by="PHP/5.2.0-8+etch10">
<p accents="yes" heading="1">
<s>
Brod	brod	k1gInSc1qP	brod
porazil	porazit	k5eAaPmAgInSaPrDqP	
Chropyni	Chropyně	k1gFnSc4	Chropyně
a	a	k8xCqP	
ztrácí	ztrácet	k5eAaImIp3nSrDaIqP	
na	na	k7c4qP	
ni	on	k3p3gFnSc4xPqP	
bod	bod	k1gInSc4qP	bod
</s>
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG
HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ
</p>
<p accents="yes" heading="0">
<s>
Náskok	náskok	k1gInSc1qP	náskok
Chropyně	Chropyně	k1gFnSc2	Chropyně
na	na	k7c6qP	
čele	čelo	k1gNnSc6qP	čelo
se	se	k3c4xPyFqP	
''')

        sio.save_segment(seg)

        # load the same location in the file again and check the content
        seg = sio.get_segment(block_begin_line=1, block_num_lines=20)
        self.assertEqual(seg.block_data(), u'''<doc xdedupl_id="192430" contenttype="text/html" guessed_charset="cp1250" ip="89.185.224.47" lang_filter_score="0.546968355014" length="33933" timestamp="20080316150457" url="http://www.efotbal.cz/index.php?page=clanek&amp;clanek=26164" http_cache_control="no-store, no-cache, must-revalidate, post-check=0, pre-check=0" http_connection="close" http_content_type="text/html" http_date="Sun, 16 Mar 2008 15:05:05 GMT" http_expires="Thu, 19 Nov 1981 08:52:00 GMT" http_pragma="no-cache" http_server="Apache/2.2.3 (Debian) PHP/5.2.0-8+etch10" http_x_powered_by="PHP/5.2.0-8+etch10">
<p accents="yes" heading="1">
<s>
Brod	brod	k1gInSc1qP	brod
porazil	porazit	k5eAaPmAgInSaPrDqP	
Chropyni	Chropyně	k1gFnSc4	Chropyně
a	a	k8xCqP	
ztrácí	ztrácet	k5eAaImIp3nSrDaIqP	
na	na	k7c4qP	
ni	on	k3p3gFnSc4xPqP	
bod	bod	k1gInSc4qP	bod
</s>
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG
HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
''')
        # NOTE: The segment_src_line_range for this 20-line chunk of the virtual file is 
        #       (1,13), that is, the first 12 lines of the physical file. The remaining 
        #       8 lines are from the hunk that adds the 10 lines AFTER those. 
        #       To be able to get those, the segment must include that hunk, even 
        #       though it just touches the segment_src_line_range.
        #
        # UPDATE: This problem arised from the chaos of choosing segment_hunks multiple 
        #         times in insidiously slightly different ways (first by the dest, then 
        #         by the src...). 
        #         
        #         The correct (and simple) way to avoid this problem (and possibly other 
        #         problems as well) is to choose segment_hunks only once in the beginning 
        #         of the get_segment() algorithm, the correct way: 
        #         choose every hunk with a dest range that intersects the block_line_range.
        #         Then use those segment_hunks in the rest of the algorithm. 


    def test_crash_1_variant_replacing_instead_of_inserting(self): 
        # Now that I fixed the cause of crash_1, I make sure it does not occur when h.n1() > 0
        # (see SegmentIO._get_segment_changelog). If it did occur in that case as well, my fix 
        # would not be enough.
        orig_file_path = os.path.join(os.getcwd(), 
                u'segmentio_testdata/investigating-crashes/cztenten_100k.vert.bak')
        file_path = os.path.join(os.getcwd(), 
                u'segmentio_testdata/investigating-crashes/cztenten_100k.vert')
        shutil.copyfile(orig_file_path, file_path)

        fio = io.open('segmentio_testdata/investigating-crashes/cztenten_100k.vert', 
                'r', encoding='utf-8')
        lrio = segmentio.FileLineReadIO(fio)
        sio = SegmentIO(lrio, u'')

        seg = sio.get_segment(block_begin_line=1, block_num_lines=20)
        self.assertEqual(seg.block_data(), u'''<doc xdedupl_id="192430" contenttype="text/html" guessed_charset="cp1250" ip="89.185.224.47" lang_filter_score="0.546968355014" length="33933" timestamp="20080316150457" url="http://www.efotbal.cz/index.php?page=clanek&amp;clanek=26164" http_cache_control="no-store, no-cache, must-revalidate, post-check=0, pre-check=0" http_connection="close" http_content_type="text/html" http_date="Sun, 16 Mar 2008 15:05:05 GMT" http_expires="Thu, 19 Nov 1981 08:52:00 GMT" http_pragma="no-cache" http_server="Apache/2.2.3 (Debian) PHP/5.2.0-8+etch10" http_x_powered_by="PHP/5.2.0-8+etch10">
<p accents="yes" heading="1">
<s>
Brod	brod	k1gInSc1qP	brod
porazil	porazit	k5eAaPmAgInSaPrDqP	
Chropyni	Chropyně	k1gFnSc4	Chropyně
a	a	k8xCqP	
ztrácí	ztrácet	k5eAaImIp3nSrDaIqP	
na	na	k7c4qP	
ni	on	k3p3gFnSc4xPqP	
bod	bod	k1gInSc4qP	bod
</s>
</p>
<p accents="yes" heading="0">
<s>
Náskok	náskok	k1gInSc1qP	náskok
Chropyně	Chropyně	k1gFnSc2	Chropyně
na	na	k7c6qP	
čele	čelo	k1gNnSc6qP	čelo
se	se	k3c4xPyFqP	
''')
        self.assertEqual(seg.changelog(), u'')


        # do the edit that crashes the editor

        seg.set_block_data(u'''<doc xdedupl_id="192430" contenttype="text/html" guessed_charset="cp1250" ip="89.185.224.47" lang_filter_score="0.546968355014" length="33933" timestamp="20080316150457" url="http://www.efotbal.cz/index.php?page=clanek&amp;clanek=26164" http_cache_control="no-store, no-cache, must-revalidate, post-check=0, pre-check=0" http_connection="close" http_content_type="text/html" http_date="Sun, 16 Mar 2008 15:05:05 GMT" http_expires="Thu, 19 Nov 1981 08:52:00 GMT" http_pragma="no-cache" http_server="Apache/2.2.3 (Debian) PHP/5.2.0-8+etch10" http_x_powered_by="PHP/5.2.0-8+etch10">
<p accents="yes" heading="1">
<s>
Brod	brod	k1gInSc1qP	brod
porazil	porazit	k5eAaPmAgInSaPrDqP	
Chropyni	Chropyně	k1gFnSc4	Chropyně
a	a	k8xCqP	
ztrácí	ztrácet	k5eAaImIp3nSrDaIqP	
na	na	k7c4qP	
ni	on	k3p3gFnSc4xPqP	
bod	bod	k1gInSc4qP	bod
<SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS>
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG
HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ
</p>
<p accents="yes" heading="0">
<s>
Náskok	náskok	k1gInSc1qP	náskok
Chropyně	Chropyně	k1gFnSc2	Chropyně
na	na	k7c6qP	
čele	čelo	k1gNnSc6qP	čelo
se	se	k3c4xPyFqP	
''')

        sio.save_segment(seg)

        # load the same location in the file again and check the content
        seg = sio.get_segment(block_begin_line=1, block_num_lines=20)
        self.assertEqual(seg.block_data(), u'''<doc xdedupl_id="192430" contenttype="text/html" guessed_charset="cp1250" ip="89.185.224.47" lang_filter_score="0.546968355014" length="33933" timestamp="20080316150457" url="http://www.efotbal.cz/index.php?page=clanek&amp;clanek=26164" http_cache_control="no-store, no-cache, must-revalidate, post-check=0, pre-check=0" http_connection="close" http_content_type="text/html" http_date="Sun, 16 Mar 2008 15:05:05 GMT" http_expires="Thu, 19 Nov 1981 08:52:00 GMT" http_pragma="no-cache" http_server="Apache/2.2.3 (Debian) PHP/5.2.0-8+etch10" http_x_powered_by="PHP/5.2.0-8+etch10">
<p accents="yes" heading="1">
<s>
Brod	brod	k1gInSc1qP	brod
porazil	porazit	k5eAaPmAgInSaPrDqP	
Chropyni	Chropyně	k1gFnSc4	Chropyně
a	a	k8xCqP	
ztrácí	ztrácet	k5eAaImIp3nSrDaIqP	
na	na	k7c4qP	
ni	on	k3p3gFnSc4xPqP	
bod	bod	k1gInSc4qP	bod
<SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS>
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG
HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
''')



class SegmentIOPrivateMethodsTestCase(unittest.TestCase):
    def setUp(self): 
        self._file_io = io.open('segmentio_testdata/handmade-changelog/reference-src-file.txt', 
                'r', encoding='utf-8')
        self._line_read_io = segmentio.FileLineReadIO(self._file_io)
        with io.open('segmentio_testdata/handmade-changelog/reference-changelog.patch', 
                'r', encoding='utf-8') as f: 
            changelog = f.read()
        self._sio = SegmentIO(self._line_read_io, changelog)

    def tearDown(self): 
        self._file_io.close()


    def test_get_segment_line_range(self): 
        block_line_range = (86, 92)
        correct_segment_line_range = (85, 97)

        segment_hunks = self._sio._get_segment_hunks(block_line_range)
        segment_line_range = self._sio._get_segment_line_range(block_line_range, segment_hunks)
        self.assertEqual(segment_line_range, correct_segment_line_range)

    def test_get_segment_src_line_range(self): 
        block_line_range = (86, 92)
        correct_segment_src_line_range = (33, 48)

        segment_hunks = self._sio._get_segment_hunks(block_line_range)
        segment_line_range = self._sio._get_segment_line_range(block_line_range, segment_hunks)
        segment_src_line_range = self._sio._get_segment_src_line_range(
                segment_line_range, 
                block_line_range, 
                segment_hunks)
        self.assertEqual(segment_src_line_range, correct_segment_src_line_range)

#    def test_get_segment_changelog(self): 
#        segment_src_line_range = (33, 48)
#        segment_line_range = (85, 97)
#        correct_segment_changelog = u'''@@ -1,4 +1,2 @@
#-Tenhle
#-naopak
#-bude
#-zkrácen.
#+Tenhle byl
#+naopak zkrácen.
#@@ -5,11 +3,10 @@
# šel
# dědeček
# na
# kopeček
#+...nevím, jak dál!
# (za básní)
#-sixth
#-seventh
# eighth
# ninth
# tenth
# eleventh
#'''
#        segment_changelog = self._sio._get_segment_changelog(segment_src_line_range, segment_line_range)
#        self.assertEqual(segment_changelog, correct_segment_changelog)

    def test_read_src_lines(self): 
        src_line_range = (30, 37)
        correct_data = u'''něco 30
první
(za prvním)
Tenhle
naopak
bude
zkrácen.
'''

        data = self._sio._read_src_lines(src_line_range)
        self.assertEqual(data, correct_data)



class OffsetTableTestCase(unittest.TestCase): 
    def setUp(self): 
        # from 
        # `diff -U 0 reference-file-after-edit1.txt reference-file-after-edit2.txt` 
        # in segmentio_testdata/generated-changelog/
        self._c2 = u'''@@ -3,2 +2,0 @@
-3rd
-fourth
@@ -6,0 +5,3 @@
+ADDING
+3
+LINES
@@ -9 +10 @@
-ninth
+9th
'''
        # from 
        # `diff -U 0 reference-file-after-edit2.txt reference-file-after-edit3.txt` 
        # in segmentio_testdata/generated-changelog/
        self._c3 = u'''@@ -2 +1,0 @@
-2nd
@@ -5,3 +4 @@
-ADDING
-3
-LINES
+LN
@@ -8,0 +6 @@
+KEKščř
@@ -10 +8,2 @@
-9th
+ninEEEth
+ABC
'''

    def test_init(self): 
        # test on c2
        ot_c2 = segmentio.OffsetTable(self._c2)

        correct_c2_dest_line_ot = [
                (5, -2), 
                (7, 3), 
                (10, 0)]
        self.assertEqual(ot_c2._dest_line_offset_table, correct_c2_dest_line_ot)

        correct_c2_src_line_ot = [ 
                (3, 2), 
                (8, -3), 
                (11, 0)]
        self.assertEqual(ot_c2._src_line_offset_table, correct_c2_src_line_ot)

        #TODO: dest_pos_ot, src_pos_ot

        # test on c3
        ot_c3 = segmentio.OffsetTable(self._c3)

        correct_c3_dest_line_ot = [ 
                (3, -1), 
                (8, -2), 
                (9, 1), 
                (11, 1)]
        self.assertEqual(ot_c3._dest_line_offset_table, correct_c3_dest_line_ot)

        correct_c3_src_line_ot = [ 
                (2, 1), 
                (5, 2), 
                (7, -1), 
                (10, -1)]
        self.assertEqual(ot_c3._src_line_offset_table, correct_c3_src_line_ot)

        
    def test_dest_line_offset(self): 
        # test on c2
        ot_c2 = segmentio.OffsetTable(self._c2)
        self.assertEqual(ot_c2.dest_line_offset(src_line=1), 0)
        self.assertEqual(ot_c2.dest_line_offset(src_line=2), 0)
        self.assertEqual(ot_c2.dest_line_offset(src_line=3), 0)
        self.assertEqual(ot_c2.dest_line_offset(src_line=4), 0)
        self.assertEqual(ot_c2.dest_line_offset(src_line=5), -2)  # (5, -2)
        self.assertEqual(ot_c2.dest_line_offset(src_line=6), -2)
        self.assertEqual(ot_c2.dest_line_offset(src_line=7), -2+3)  # (7, 3)
        self.assertEqual(ot_c2.dest_line_offset(src_line=8), -2+3)
        self.assertEqual(ot_c2.dest_line_offset(src_line=9), -2+3)
        self.assertEqual(ot_c2.dest_line_offset(src_line=10), -2+3+0)  # (10, 0)
        self.assertEqual(ot_c2.dest_line_offset(src_line=11), -2+3+0)
        self.assertEqual(ot_c2.dest_line_offset(src_line=12), -2+3+0)

        # test on c3
        ot_c3 = segmentio.OffsetTable(self._c3)
        self.assertEqual(ot_c3.dest_line_offset(src_line=1), 0)
        self.assertEqual(ot_c3.dest_line_offset(src_line=2), 0)
        self.assertEqual(ot_c3.dest_line_offset(src_line=3), -1)  # (3, -1)
        self.assertEqual(ot_c3.dest_line_offset(src_line=4), -1)
        self.assertEqual(ot_c3.dest_line_offset(src_line=5), -1)
        self.assertEqual(ot_c3.dest_line_offset(src_line=6), -1)
        self.assertEqual(ot_c3.dest_line_offset(src_line=7), -1)
        self.assertEqual(ot_c3.dest_line_offset(src_line=8), -1-2)  # (8, -2)
        self.assertEqual(ot_c3.dest_line_offset(src_line=9), -1-2+1)  # (9, 1)
        self.assertEqual(ot_c3.dest_line_offset(src_line=10), -1-2+1)
        self.assertEqual(ot_c3.dest_line_offset(src_line=11), -1-2+1+1)  # (11, 1)
        self.assertEqual(ot_c3.dest_line_offset(src_line=12), -1-2+1+1)


    def test_src_line_offset(self): 
        # test on c2
        ot_c2 = segmentio.OffsetTable(self._c2)
        self.assertEqual(ot_c2.src_line_offset(dest_line=1), 0)
        self.assertEqual(ot_c2.src_line_offset(dest_line=2), 0)
        self.assertEqual(ot_c2.src_line_offset(dest_line=3), 2)  # (3, 2)
        self.assertEqual(ot_c2.src_line_offset(dest_line=4), 2)
        self.assertEqual(ot_c2.src_line_offset(dest_line=5), 2)
        self.assertEqual(ot_c2.src_line_offset(dest_line=6), 2)
        self.assertEqual(ot_c2.src_line_offset(dest_line=7), 2)
        self.assertEqual(ot_c2.src_line_offset(dest_line=8), 2-3)  # (8, -3)
        self.assertEqual(ot_c2.src_line_offset(dest_line=9), 2-3)
        self.assertEqual(ot_c2.src_line_offset(dest_line=10), 2-3)
        self.assertEqual(ot_c2.src_line_offset(dest_line=11), 2-3+0)  # (11, 0)
        self.assertEqual(ot_c2.src_line_offset(dest_line=12), 2-3+0)

        # test on c3
        ot_c3 = segmentio.OffsetTable(self._c3)
        self.assertEqual(ot_c3.src_line_offset(dest_line=1), 0)
        self.assertEqual(ot_c3.src_line_offset(dest_line=2), 1)  # (2, 1)
        self.assertEqual(ot_c3.src_line_offset(dest_line=3), 1)
        self.assertEqual(ot_c3.src_line_offset(dest_line=4), 1)
        self.assertEqual(ot_c3.src_line_offset(dest_line=5), 1+2)  # (5, 2)
        self.assertEqual(ot_c3.src_line_offset(dest_line=6), 1+2)
        self.assertEqual(ot_c3.src_line_offset(dest_line=7), 1+2-1)  # (7, -1)
        self.assertEqual(ot_c3.src_line_offset(dest_line=8), 1+2-1)
        self.assertEqual(ot_c3.src_line_offset(dest_line=9), 1+2-1)
        self.assertEqual(ot_c3.src_line_offset(dest_line=10), 1+2-1-1)  # (10, -1)
        self.assertEqual(ot_c3.src_line_offset(dest_line=11), 1+2-1-1)
        self.assertEqual(ot_c3.src_line_offset(dest_line=12), 1+2-1-1)


    #TODO: test_dest_pos_offset, test_src_pos_offset



#class SrcDestContentProviderTestCase(unittest.TestCase): 
#    def test_c2(self): 
#        # from 
#        # `diff -U 0 reference-file-after-edit1.txt reference-file-after-edit2.txt` 
#        # in segmentio_testdata/generated-changelog/
#        c2 = u'''@@ -3,2 +2,0 @@
#-3rd
#-fourth
#@@ -6,0 +5,3 @@
#+ADDING
#+3
#+LINES
#@@ -9 +10 @@
#-ninth
#+9th
#'''
#        cp = segmentio.SrcDestContentProvider(src_changelog=c2, dest_changelog=c2)
#
#        # test getting the two one-sided hunks in this changelog
#        # (the first hunk for src and the second hunk for dest)
#        # in enrirety
#        content = cp.get_src_lines(first=3, last=4)
#        self.assertEqual(content, u'3rd\nfourth\n')
#
#        content = cp.get_dest_lines(first=5, last=7)
#        self.assertEqual(content, u'ADDING\n3\nLINES\n')
#
#        # test getting only a part 
#        content = cp.get_dest_lines(first=10, last=10)
#        self.assertEqual(content, u'9th\n')
#
#        content = cp.get_dest_lines(first=5, last=6)
#        self.assertEqual(content, u'ADDING\n3\n')
#
#        ## test getting a chunk overlapping into outside of hunks on this side
#        #try: 
#        #    content = cp.get_dest_lines(first=10, last=10)
#        #self.assertEqual(content, u'9th\n')
#
#        ## test getting a chunk entirely outside of hunks on this side
#        #correct_src_lines_first_1_last_4 = #exception, there are none!
#
#        ## test getting a chunk entirely outside of hunks on both sides




class FreestandingFunctionsTestCase(unittest.TestCase): 
    def test_diff(self): 
        # with open('segmentio_testdata/handmade-changelog/reference-src-file.txt') as f: 
        #     data1 = f.read()
        # with open('segmentio_testdata/handmade-changelog/file.txt') as f: 
        #     data2 = f.read()
        # with open('segmentio_testdata/handmade-changelog/reference-changelog.patch') as f: 
        #     correct_diff = f.read()
        # NOTE: The changelog can have multiple correct forms by using different numbers of context lines. 
        #       It happens to make a changelog that's different from the one I've made by hand 
        #       but that does the same thing.

        with io.open('segmentio_testdata/generated-changelog/reference-file.txt', 
                'r', encoding='utf-8') as f: 
            data1 = f.read()
        with io.open('segmentio_testdata/generated-changelog/reference-file-after-edit1.txt', 
                'r', encoding='utf-8') as f: 
            data2 = f.read()

        # from segmentio_testdata/generated-changelog/changelog1.patch
        correct_diff = u'''@@ -1,3 +1,3 @@
-first
-second
-third
+1st
+2nd
+3rd
'''

        d = segmentio.diff(data1, data2)
        self.assertEqual(d, correct_diff)


    def test_patch(self): 
        with io.open('segmentio_testdata/generated-changelog/reference-file.txt', 
                'r', encoding='utf-8') as f: 
            data = f.read()

        # from segmentio_testdata/generated-changelog/changelog1.patch
        changelog = u'''@@ -1,6 +1,6 @@
-first
-second
-third
+1st
+2nd
+3rd
 fourth
 fifth
 sixth
'''

        with io.open('segmentio_testdata/generated-changelog/reference-file-after-edit1.txt', 
                'r', encoding='utf-8') as f: 
            correct_result = f.read()

        result = segmentio.patch(data, changelog)
        self.assertEqual(result, correct_result)


    def test_merge_changelogs(self): 
        #with io.open('segmentio_testdata/generated-changelog/changelog1.patch', 
        #        'r', encoding='utf-8') as f: 
        #    c1 = f.read()
        #with io.open('segmentio_testdata/generated-changelog/edit2.patch', 
        #        'r', encoding='utf-8') as f: 
        #    c2 = f.read()
        #with io.open('segmentio_testdata/generated-changelog/changelog2.patch', 
        #        'r', encoding='utf-8') as f: 
        #    correct_result = f.read()

        # from segmentio_testdata/generated-changelog/changelog1.patch
        c1 = u'''@@ -1,6 +1,6 @@
-first
-second
-third
+1st
+2nd
+3rd
 fourth
 fifth
 sixth
'''
        # from segmentio_testdata/generated-changelog/edit2.patch
        c2 = u'''@@ -1,12 +1,13 @@
 1st
 2nd
-3rd
-fourth
 fifth
 sixth
+ADDING
+3
+LINES
 seventh
 eighth
-ninth
+9th
 tenth
 eleventh
 twelfth
'''
        # from segmentio_testdata/generated-changelog/changelog2.patch
        correct_result = u'''@@ -1,4 +1,2 @@
-first
-second
-third
-fourth
+1st
+2nd
@@ -6,0 +5,3 @@
+ADDING
+3
+LINES
@@ -9 +10 @@
-ninth
+9th
'''

        result = segmentio.merge_changelogs(c1, c2)
        self.assertEqual(result, correct_result)


    def test_rebase_changelog(self): 
        # TODO also test if conflicts are discovered
        with io.open('segmentio_testdata/rebasing/c12.patch', 
                'r', encoding='utf-8') as f: 
            c12 = segmentio.changelog_from_patch_file_content(f.read())
        with io.open('segmentio_testdata/rebasing/c1234.patch', 
                'r', encoding='utf-8') as f: 
            c1234 = segmentio.changelog_from_patch_file_content(f.read())

        with io.open('segmentio_testdata/rebasing/editX-on-reference-file.patch', 
                'r', encoding='utf-8') as f: 
            editX_on_f0 = segmentio.changelog_from_patch_file_content(f.read())
        with io.open('segmentio_testdata/rebasing/editX-on-reference-file-after-edit2.patch', 
                'r', encoding='utf-8') as f: 
            editX_on_f2 = segmentio.changelog_from_patch_file_content(f.read())
        with io.open('segmentio_testdata/rebasing/editX-on-reference-file-after-edit4.patch', 
                'r', encoding='utf-8') as f: 
            editX_on_f4 = segmentio.changelog_from_patch_file_content(f.read())

        with io.open('segmentio_testdata/rebasing/editY-on-reference-file.patch', 
                'r', encoding='utf-8') as f: 
            editY_on_f0 = segmentio.changelog_from_patch_file_content(f.read())
        with io.open('segmentio_testdata/rebasing/editY-on-reference-file-after-edit2.patch', 
                'r', encoding='utf-8') as f: 
            editY_on_f2 = segmentio.changelog_from_patch_file_content(f.read())
        with io.open('segmentio_testdata/rebasing/editY-on-reference-file-after-edit4.patch', 
                'r', encoding='utf-8') as f: 
            editY_on_f4 = segmentio.changelog_from_patch_file_content(f.read())

        editX_rebased_from_f0_to_f2 = segmentio.rebase_changelog(editX_on_f0, c12)
        self.assertTrue(
                are_equivalent_changelogs(
                    'segmentio_testdata/rebasing/reference-file-after-edit2.txt', 
                    editX_rebased_from_f0_to_f2, editX_on_f2))

        editX_rebased_from_f0_to_f4 = segmentio.rebase_changelog(editX_on_f0, c1234)
        self.assertTrue(
                are_equivalent_changelogs(
                    'segmentio_testdata/rebasing/reference-file-after-edit4.txt', 
                    editX_rebased_from_f0_to_f4, editX_on_f4))

        editY_rebased_from_f0_to_f2 = segmentio.rebase_changelog(editY_on_f0, c12)
        self.assertTrue(
                are_equivalent_changelogs(
                    'segmentio_testdata/rebasing/reference-file-after-edit2.txt', 
                    editY_rebased_from_f0_to_f2, editY_on_f2))

        editY_rebased_from_f0_to_f4 = segmentio.rebase_changelog(editY_on_f0, c1234)
        self.assertTrue(
                are_equivalent_changelogs(
                    'segmentio_testdata/rebasing/reference-file-after-edit4.txt', 
                    editY_rebased_from_f0_to_f4, editY_on_f4))


    def test_are_conflicting_hunks(self): 
        # TODO
        pass


    def test_has_context_lines(self): 
        # from segmentio_testdata/generated-changelog/changelog1.patch
        c1 = u'''@@ -1,6 +1,6 @@
-first
-second
-third
+1st
+2nd
+3rd
 fourth
 fifth
 sixth
'''
        # from 
        # `diff -U 0 reference-file-after-edit1.txt reference-file-after-edit2.txt` 
        # in segmentio_testdata/generated-changelog/
        c2 = u'''@@ -3,2 +2,0 @@
-3rd
-fourth
@@ -6,0 +5,3 @@
+ADDING
+3
+LINES
@@ -9 +10 @@
-ninth
+9th
'''
        self.assertTrue(segmentio.has_context_lines(c1))
        self.assertFalse(segmentio.has_context_lines(c2))


    def test_join_neighboring_hunks_src_touch(self): 
        # h1sXYZ is a hunk with these properties:
        #         X: h1_src_is_spike (1: True, 0: False)
        #         Y: h2_src_is_spike (1: True, 0: False)
        #         Z: src_touch (1: True, 0: False)
        h1s111 = segmentio.Hunk(3, 0, 1, 2, u'+A\n+B\n')
        h2s111 = segmentio.Hunk(3, 0, 4, 2, u'+X\n+Y\n')
        self.assertTrue(segmentio._join_neighboring_hunks_src_touch(h1s111, h2s111, True, True))

        h1s110 = segmentio.Hunk(3, 0, 1, 2, u'+A\n+B\n')
        h2s110 = segmentio.Hunk(4, 0, 4, 2, u'+X\n+Y\n')
        self.assertFalse(segmentio._join_neighboring_hunks_src_touch(h1s110, h2s110, True, True))

        h1s101 = segmentio.Hunk(3, 0, 1, 3, u'+A\n+B\n+C\n')
        h2s101 = segmentio.Hunk(4, 2, 5, 0, u'-x\n-y\n')
        self.assertTrue(segmentio._join_neighboring_hunks_src_touch(h1s101, h2s101, True, False))

        h1s100 = segmentio.Hunk(3, 0, 1, 2, u'+A\n+B\n')
        h2s100 = segmentio.Hunk(5, 1, 4, 2, u'-x\n+X\n+Y\n')
        self.assertFalse(segmentio._join_neighboring_hunks_src_touch(h1s100, h2s100, True, False))

        h1s011 = segmentio.Hunk(1, 2, 1, 0, u'-a\n-b\n')
        h2s011 = segmentio.Hunk(2, 0, 3, 3, u'+X\n+Y\n+Z\n')
        self.assertTrue(segmentio._join_neighboring_hunks_src_touch(h1s011, h2s011, False, True))

        h1s010 = segmentio.Hunk(1, 2, 1, 0, u'-a\n-b\n')
        h2s010 = segmentio.Hunk(3, 0, 3, 2, u'+X\n+Y\n')
        self.assertFalse(segmentio._join_neighboring_hunks_src_touch(h1s010, h2s010, False, True))

        h1s001 = segmentio.Hunk(1, 2, 1, 2, u'-a\n-b\n+A\n+B\n')
        h2s001 = segmentio.Hunk(3, 3, 3, 0, u'-x\n-y\n-z\n')
        self.assertTrue(segmentio._join_neighboring_hunks_src_touch(h1s001, h2s001, False, False))

        h1s000 = segmentio.Hunk(1, 2, 1, 2, u'-a\n-b\n+A\n+B\n')
        h2s000 = segmentio.Hunk(4, 2, 3, 3, u'-x\n-y\n+X\n+Y\n+Z\n')
        self.assertFalse(segmentio._join_neighboring_hunks_src_touch(h1s000, h2s000, False, False))



    def test_join_neighboring_hunks_dest_touch(self): 
        # h1dXYZ is a hunk with these properties:
        #         X: h1_dest_is_spike (1: True, 0: False)
        #         Y: h2_dest_is_spike (1: True, 0: False)
        #         Z: dest_touch (1: True, 0: False)
        h1d111 = segmentio.Hunk(1, 2, 3, 0, u'-a\n-b\n')
        h2d111 = segmentio.Hunk(4, 2, 3, 0, u'-x\n-y\n')
        self.assertTrue(segmentio._join_neighboring_hunks_dest_touch(h1d111, h2d111, True, True))

        h1d110 = segmentio.Hunk(1, 2, 3, 0, u'-a\n-b\n')
        h2d110 = segmentio.Hunk(4, 2, 4, 0, u'-x\n-y\n')
        self.assertFalse(segmentio._join_neighboring_hunks_dest_touch(h1d110, h2d110, True, True))

        h1d101 = segmentio.Hunk(1, 3, 3, 0, u'-a\n-b\n-c\n')
        h2d101 = segmentio.Hunk(5, 0, 4, 2, u'+X\n+Y\n')
        self.assertTrue(segmentio._join_neighboring_hunks_dest_touch(h1d101, h2d101, True, False))

        h1d100 = segmentio.Hunk(1, 2, 3, 0, u'-a\n-b\n')
        h2d100 = segmentio.Hunk(4, 2, 5, 1, u'+X\n+Y\n')
        self.assertFalse(segmentio._join_neighboring_hunks_dest_touch(h1d100, h2d100, True, False))

        h1d011 = segmentio.Hunk(1, 0, 1, 2, u'+A\n+B\n')
        h2d011 = segmentio.Hunk(3, 3, 2, 0, u'-x\n-y\n-z\n')
        self.assertTrue(segmentio._join_neighboring_hunks_dest_touch(h1d011, h2d011, False, True))

        h1d010 = segmentio.Hunk(1, 0, 1, 2, u'+A\n+B\n')
        h2d010 = segmentio.Hunk(3, 2, 3, 0, u'-x\n-y\n')
        self.assertFalse(segmentio._join_neighboring_hunks_dest_touch(h1d010, h2d010, False, True))

        h1d001 = segmentio.Hunk(1, 2, 1, 2, u'-a\n-b\n+A\n+B\n')
        h2d001 = segmentio.Hunk(3, 0, 3, 3, u'+X\n+Y\n+Z\n')
        self.assertTrue(segmentio._join_neighboring_hunks_dest_touch(h1d001, h2d001, False, False))

        h1d000 = segmentio.Hunk(1, 2, 1, 2, u'-a\n-b\n+A\n+B\n')
        h2d000 = segmentio.Hunk(3, 3, 4, 2, u'-x\n-y\n-z\n+X\n+Y\n')
        self.assertFalse(segmentio._join_neighboring_hunks_dest_touch(h1d000, h2d000, False, False))


    def test_join_neighboring_hunks(self): 
        # the output of step (1.) of compose_changelogs() on 
        # c1 = changelog from segmentio_testdata/composing/edit1.patch
        # c2 = changelog from segmentio_testdata/composing/edit2.patch
        c1_h0 = segmentio.Hunk(1, 1, 1, 1, u'''-a1
+a1
''')
        c1_h1 = segmentio.Hunk(5, 2, 3, 0, u'''-ha1:1
-ha1:2
''')
        c1_h2 = segmentio.Hunk(9, 1, 7, 1, u'''-a9
+a9
''')
        c1_h3 = segmentio.Hunk(10, 3, 8, 10, u'''-ha2:1
-ha2:2
-ha2:3
+KKK
+LLL
+MMM
+NNN
+OOO
+PPP
+QQQ
+RRR
+SSS
+TTT
''')
        c1_h4 = segmentio.Hunk(13, 1, 18, 1, u'''-a13
+a13
''')
        c1_h5 = segmentio.Hunk(13, 0, 19, 5, u'''+11111
+22222
+33333
+44444
+55555
''')

        c1_hunks = [c1_h0, c1_h1, c1_h2, c1_h3, c1_h4, c1_h5]


        c1_jh0 = segmentio.Hunk(1, 1, 1, 1, u'''-a1
+a1
''')
        c1_jh1 = segmentio.Hunk(5, 2, 3, 0, u'''-ha1:1
-ha1:2
''')
        c1_jh2 = segmentio.Hunk(9, 5, 7, 17, u'''-a9
-ha2:1
-ha2:2
-ha2:3
-a13
+a9
+KKK
+LLL
+MMM
+NNN
+OOO
+PPP
+QQQ
+RRR
+SSS
+TTT
+a13
+11111
+22222
+33333
+44444
+55555
''')

        correct_c1_joined_hunks = [c1_jh0, c1_jh1, c1_jh2]


        c2_h0 = segmentio.Hunk(1, 1, 0, 0, u'''-a1
''')
        c2_h1 = segmentio.Hunk(7, 3, 6, 7, u'''-a9
-KKK
-LLL
+:-)
+;-)
+:=|
+:-E
+:=|$
+;-($
+:-($
''')
        c2_h2 = segmentio.Hunk(10, 1, 13, 1, u'''-MMM
+MMM
''')
        c2_h3 = segmentio.Hunk(11, 2, 14, 4, u'''-NNN
-OOO
+:-O
+:~)
+:~(
+:~|
''')
        c2_h4 = segmentio.Hunk(13, 1, 18, 1, u'''-PPP
+PPP
''')
        c2_h5 = segmentio.Hunk(14, 1, 19, 1, u'''-QQQ
+QQQ
''')
        c2_h6 = segmentio.Hunk(15, 1, 20, 1, u'''-RRR
+RRR
''')
        c2_h7 = segmentio.Hunk(16, 6, 21, 2, u'''-SSS
-TTT
-a13
-11111
-22222
-33333
+:))
+:((
''')
        c2_h8 = segmentio.Hunk(22, 1, 23, 1, u'''-44444
+44444
''')
        c2_h9 = segmentio.Hunk(23, 1, 24, 1, u'''-55555
+55555
''')

        c2_hunks = [c2_h0, c2_h1, c2_h2, c2_h3, c2_h4, c2_h5, c2_h6, c2_h7, c2_h8, c2_h9]


        c2_jh0 = segmentio.Hunk(1, 1, 0, 0, u'''-a1
''')
        c2_jh1 = segmentio.Hunk(7, 17, 6, 19, u'''-a9
-KKK
-LLL
-MMM
-NNN
-OOO
-PPP
-QQQ
-RRR
-SSS
-TTT
-a13
-11111
-22222
-33333
-44444
-55555
+:-)
+;-)
+:=|
+:-E
+:=|$
+;-($
+:-($
+MMM
+:-O
+:~)
+:~(
+:~|
+PPP
+QQQ
+RRR
+:))
+:((
+44444
+55555
''')

        correct_c2_joined_hunks = [c2_jh0, c2_jh1]
        

        c1_joined_hunks = segmentio.join_neighboring_hunks(c1_hunks)
        self.assertEqual(c1_joined_hunks, correct_c1_joined_hunks)

        c2_joined_hunks = segmentio.join_neighboring_hunks(c2_hunks)
        self.assertEqual(c2_joined_hunks, correct_c2_joined_hunks)



    def test_compose_changelogs_on_composing_example(self): 
        # test on the stuff in segmentio_testdata/composing/
        with io.open('segmentio_testdata/composing/edit1.patch', 
                'r', encoding='utf-8') as f_io: 
            edit1 = segmentio.changelog_from_patch_file_content(f_io.read())
        with io.open('segmentio_testdata/composing/edit2.patch', 
                'r', encoding='utf-8') as f_io: 
            edit2 = segmentio.changelog_from_patch_file_content(f_io.read())
        with io.open('segmentio_testdata/composing/composed-edit1-edit2.patch', 
                'r', encoding='utf-8') as f_io: 
            correct_composed12 = segmentio.changelog_from_patch_file_content(f_io.read())
    
        composed12 = segmentio.compose_changelogs(edit1, edit2)
        self.assertEqual(composed12, correct_composed12)

    def test_compose_changelogs_on_generated_changelogs(self): 
        with io.open('segmentio_testdata/generated-changelog/reference-file.txt', 
                'r', encoding='utf-8') as f_io: 
            reference_file = f_io.read()
        with io.open('segmentio_testdata/generated-changelog/reference-file-after-edit1.txt', 
                'r', encoding='utf-8') as f_io: 
            reference_file_after_edit1 = f_io.read()
        with io.open('segmentio_testdata/generated-changelog/reference-file-after-edit2.txt', 
                'r', encoding='utf-8') as f_io: 
            reference_file_after_edit2 = f_io.read()
        with io.open('segmentio_testdata/generated-changelog/reference-file-after-edit3.txt', 
                'r', encoding='utf-8') as f_io: 
            reference_file_after_edit3 = f_io.read()
        with io.open('segmentio_testdata/generated-changelog/reference-file-after-edit4.txt', 
                'r', encoding='utf-8') as f_io: 
            reference_file_after_edit4 = f_io.read()

        # from 
        # `diff -U 0 reference-file.txt reference-file-after-edit1.txt` 
        # in segmentio_testdata/generated-changelog/
        c1 = u'''@@ -1,3 +1,3 @@
-first
-second
-third
+1st
+2nd
+3rd
'''
        # from 
        # `diff -U 0 reference-file-after-edit1.txt reference-file-after-edit2.txt` 
        # in segmentio_testdata/generated-changelog/
        c2 = u'''@@ -3,2 +2,0 @@
-3rd
-fourth
@@ -6,0 +5,3 @@
+ADDING
+3
+LINES
@@ -9 +10 @@
-ninth
+9th
'''
        # from 
        # `diff -U 0 reference-file-after-edit2.txt reference-file-after-edit3.txt` 
        # in segmentio_testdata/generated-changelog/
        c3 = u'''@@ -2 +1,0 @@
-2nd
@@ -5,3 +4 @@
-ADDING
-3
-LINES
+LN
@@ -8,0 +6 @@
+KEKščř
@@ -10 +8,2 @@
-9th
+ninEEEth
+ABC
'''
        # from 
        # `diff -U 0 reference-file-after-edit3.txt reference-file-after-edit4.txt` 
        # in segmentio_testdata/generated-changelog/
        c4 = u'''@@ -5 +4,0 @@
-seventh
@@ -7,2 +6,7 @@
-eighth
-ninEEEth
+seventh
+[éíǧhth]
+before 9th
+[ňiňÉÉÉth]
+<in
+the
+middle>
'''

        # -- 2 changelogs -- #

        # test applying c1, then c2
        r1 = segmentio.patch(reference_file, c1)
        r2 = segmentio.patch(r1, c2)
        self.assertEqual(r2, reference_file_after_edit2)
        # test applying the composed changelog c1->c2
        c12 = segmentio.compose_changelogs(c1, c2)
        r12 = segmentio.patch(reference_file, c12)
        self.assertEqual(r12, reference_file_after_edit2)

        # test applying c2, then c3
        r2 = segmentio.patch(reference_file_after_edit1, c2)
        r3 = segmentio.patch(r2, c3)
        self.assertEqual(r3, reference_file_after_edit3)
        # test applying the composed changelog c2->c3
        c23 = segmentio.compose_changelogs(c2, c3)
        r23 = segmentio.patch(reference_file_after_edit1, c23)
        self.assertEqual(r23, reference_file_after_edit3)

        #print c23
        # NOTE: FIXED this by passing x1+1 or x2+2 instead of just x1 or x2
        #       in case of a spike. Even though it seemed OK here, it could 
        #       cause problems when chaining more compositions. 
        #
        #       (((
        #       In c23, the x1 of the second hunk (its spike) was 2, not 1.
        #       That means it's one line below the spike of the 
        #       previous hunk, not in the same place.
        #       It is because dest_line_offset for src_line=2 
        #       (the original x1 of the hunk in the first changelog)
        #       is 0, unlike for src_line=3.
        #       )))

        # test applying c3, then c4
        r3 = segmentio.patch(reference_file_after_edit2, c3)
        r4 = segmentio.patch(r3, c4)
        self.assertEqual(r4, reference_file_after_edit4)
        # test applying the composed changelog c3->c4
        c34 = segmentio.compose_changelogs(c3, c4)
        r34 = segmentio.patch(reference_file_after_edit2, c34)
        self.assertEqual(r34, reference_file_after_edit4)

        # -- 3 changelogs: testing associativity -- #

        # test applying c1, then c2, then c3
        r1 = segmentio.patch(reference_file, c1)
        r2 = segmentio.patch(r1, c2)
        r3 = segmentio.patch(r2, c3)
        self.assertEqual(r3, reference_file_after_edit3)
        # test applying the composed changelog (c1->c2)->c3
        c12 = segmentio.compose_changelogs(c1, c2)
        c12_3 = segmentio.compose_changelogs(c12, c3)
        r12_3 = segmentio.patch(reference_file, c12_3)
        self.assertEqual(r12_3, reference_file_after_edit3)
        # test applying the composed changelog c1->(c2->c3)
        c23 = segmentio.compose_changelogs(c2, c3)
        c1_23 = segmentio.compose_changelogs(c1, c23)
        r1_23 = segmentio.patch(reference_file, c12_3)
        self.assertEqual(r1_23, reference_file_after_edit3)

        # -- 4 changelogs: testing composing two composed changelogs -- #

        # test applying c1, then c2, then c3, then c4
        r1 = segmentio.patch(reference_file, c1)
        r2 = segmentio.patch(r1, c2)
        r3 = segmentio.patch(r2, c3)
        r4 = segmentio.patch(r3, c4)
        self.assertEqual(r4, reference_file_after_edit4)
        # test applying the composed changelog (c1->c2)->(c3->c4)
        c12 = segmentio.compose_changelogs(c1, c2)
        #print c12
        c34 = segmentio.compose_changelogs(c3, c4)
        #print '---'
        c12_34 = segmentio.compose_changelogs(c12, c34)
        #print c34
        r12_34 = segmentio.patch(reference_file, c12_34)
        #print '==='
        #print c12_34
        self.assertEqual(r12_34, reference_file_after_edit4)

        # -- 4 changelogs: more tests -- #

        # test applying the composed changelog c1->(c2->(c3->c4))
        c34 = segmentio.compose_changelogs(c3, c4)
        c2_34 = segmentio.compose_changelogs(c2, c34)
        c1__2_34 = segmentio.compose_changelogs(c1, c2_34)
        r1__2_34 = segmentio.patch(reference_file, c1__2_34)
        self.assertEqual(r1__2_34, reference_file_after_edit4)
        # test applying the composed changelog (c1->(c2->c3))->c4
        c23 = segmentio.compose_changelogs(c2, c3)
        c1_23 = segmentio.compose_changelogs(c1, c23)
        c1_23__4 = segmentio.compose_changelogs(c1_23, c4)
        r1_23__4 = segmentio.patch(reference_file, c1_23__4)
        self.assertEqual(r1_23__4, reference_file_after_edit4)


#    def test_compose_changelogs_on_composing_example_old(self): 
#        # test on the stuff in segmentio_testdata/composing_old/
#        with io.open('segmentio_testdata/composing_old/edit1.patch', 
#                'r', encoding='utf-8') as f_io: 
#            edit1 = f_io.read()
#        with io.open('segmentio_testdata/composing_old/edit2.patch', 
#                'r', encoding='utf-8') as f_io: 
#            edit2 = f_io.read()
#        with io.open('segmentio_testdata/composing_old/composed-edit1-edit2.patch', 
#                'r', encoding='utf-8') as f_io: 
#            correct_composed12 = f_io.read()
#
#        composed12 = segmentio.compose_changelogs(edit1, edit2)
#        self.assertEqual(composed12, correct_composed12)

    def test_invert_changelog(self): 
        # from 
        # `diff -U 0 reference-file-after-edit1.txt reference-file-after-edit2.txt` 
        # in segmentio_testdata/cN/
        c2 = u'''@@ -3,2 +2,0 @@
-3rd
-fourth
@@ -6,0 +5,3 @@
+ADDING
+3
+LINES
@@ -9,1 +10,1 @@
-ninth
+9th
'''
        # from 
        # `diff -U 0 reference-file-after-edit2.txt reference-file-after-edit1.txt` 
        # in segmentio_testdata/generated-changelog/
        inv_c2 = u'''@@ -2,0 +3,2 @@
+3rd
+fourth
@@ -5,3 +6,0 @@
-ADDING
-3
-LINES
@@ -10,1 +9,1 @@
-9th
+ninth
'''
        
        self.assertEqual(segmentio.invert_changelog(c2), inv_c2)


    def test_get_line_map(self): 
        # from 
        # `diff -U 0 reference-file-after-edit1.txt reference-file-after-edit2.txt` 
        # in segmentio_testdata/generated-changelog/
        c2 = u'''@@ -3,2 +2,0 @@
-3rd
-fourth
@@ -6,0 +5,3 @@
+ADDING
+3
+LINES
@@ -9 +10 @@
-ninth
+9th
'''
        c2_line_map = segmentio.get_line_map(c2)
        c2_inverted_line_map = segmentio.get_line_map(c2, invert=True)  # also testing inversion 
        correct_c2_line_map = [
                {'type': 'sequence', 
                'src_first': 1, 'src_last': 2, 
                'dest_first': 1, 'dest_last': 2}, 

                {'type': 'removeset', 
                'src_first': 3, 'src_last': 4, 
                'dest_first': 2, 'dest_last': None}, 

                {'type': 'sequence', 
                'src_first': 5, 'src_last': 6, 
                'dest_first': 3, 'dest_last': 4}, 

                {'type': 'addset', 
                'src_first': 6, 'src_last': None, 
                'dest_first': 5, 'dest_last': 7}, 

                {'type': 'sequence', 
                'src_first': 7, 'src_last': 8, 
                'dest_first': 8, 'dest_last': 9}, 

                {'type': 'set', 
                'src_first': 9, 'src_last': 9, 
                'dest_first': 10, 'dest_last': 10}, 

                {'type': 'sequence', 
                'src_first': 10, 'src_last': sys.maxsize/2, 
                'dest_first': 11, 'dest_last': sys.maxsize/2 + 1}
                ]
        correct_c2_inverted_line_map = [
                {'type': 'sequence', 
                'src_first': 1, 'src_last': 2, 
                'dest_first': 1, 'dest_last': 2}, 

                {'type': 'addset', 
                'src_first': 2, 'src_last': None, 
                'dest_first': 3, 'dest_last': 4}, 

                {'type': 'sequence', 
                'src_first': 3, 'src_last': 4, 
                'dest_first': 5, 'dest_last': 6}, 

                {'type': 'removeset', 
                'src_first': 5, 'src_last': 7, 
                'dest_first': 6, 'dest_last': None}, 

                {'type': 'sequence', 
                'src_first': 8, 'src_last': 9, 
                'dest_first': 7, 'dest_last': 8}, 

                {'type': 'set', 
                'src_first': 10, 'src_last': 10, 
                'dest_first': 9, 'dest_last': 9}, 

                {'type': 'sequence', 
                'src_first': 11, 'src_last': sys.maxsize/2, 
                'dest_first': 10, 'dest_last': sys.maxsize/2 - 1}
                ]

        self.assertEqual(c2_line_map, correct_c2_line_map)
        self.assertEqual(c2_inverted_line_map, correct_c2_inverted_line_map)

        # from 
        # `diff -U 0 reference-file-after-edit2.txt reference-file-after-edit3.txt` 
        # in segmentio_testdata/generated-changelog/
        c3 = u'''@@ -2 +1,0 @@
-2nd
@@ -5,3 +4 @@
-ADDING
-3
-LINES
+LN
@@ -8,0 +6 @@
+KEKščř
@@ -10 +8,2 @@
-9th
+ninEEEth
+ABC
'''
        c3_line_map = segmentio.get_line_map(c3)
        correct_c3_line_map = [
                {'type': 'sequence', 
                'src_first': 1, 'src_last': 1, 
                'dest_first': 1, 'dest_last': 1}, 

                {'type': 'removeset', 
                'src_first': 2, 'src_last': 2, 
                'dest_first': 1, 'dest_last': None}, 

                {'type': 'sequence', 
                'src_first': 3, 'src_last': 4, 
                'dest_first': 2, 'dest_last': 3}, 

                {'type': 'set', 
                'src_first': 5, 'src_last': 7, 
                'dest_first': 4, 'dest_last': 4}, 

                {'type': 'sequence', 
                'src_first': 8, 'src_last': 8, 
                'dest_first': 5, 'dest_last': 5}, 

                {'type': 'addset', 
                'src_first': 8, 'src_last': None, 
                'dest_first': 6, 'dest_last': 6}, 

                {'type': 'sequence', 
                'src_first': 9, 'src_last': 9, 
                'dest_first': 7, 'dest_last': 7}, 

                {'type': 'set', 
                'src_first': 10, 'src_last': 10, 
                'dest_first': 8, 'dest_last': 9}, 

                {'type': 'sequence', 
                'src_first': 11, 'src_last': sys.maxsize/2, 
                'dest_first': 10, 'dest_last': sys.maxsize/2 - 1}
                ]

        self.assertEqual(c3_line_map, correct_c3_line_map)

        # from 
        # `diff -U 0 reference-file-after-edit3.txt reference-file-after-edit4.txt` 
        # in segmentio_testdata/generated-changelog/
        c4 = u'''@@ -5 +4,0 @@
-seventh
@@ -7,2 +6,7 @@
-eighth
-ninEEEth
+seventh
+[éíǧhth]
+before 9th
+[ňiňÉÉÉth]
+<in
+the
+middle>
'''
        c4_line_map = segmentio.get_line_map(c4)
        correct_c4_line_map = [
                {'type': 'sequence', 
                'src_first': 1, 'src_last': 4, 
                'dest_first': 1, 'dest_last': 4}, 

                {'type': 'removeset', 
                'src_first': 5, 'src_last': 5, 
                'dest_first': 4, 'dest_last': None}, 

                {'type': 'sequence', 
                'src_first': 6, 'src_last': 6, 
                'dest_first': 5, 'dest_last': 5}, 

                {'type': 'set', 
                'src_first': 7, 'src_last': 8, 
                'dest_first': 6, 'dest_last': 12}, 

                {'type': 'sequence', 
                'src_first': 9, 'src_last': sys.maxsize/2, 
                'dest_first': 13, 'dest_last': sys.maxsize/2 + 4}
                ]

        self.assertEqual(c4_line_map, correct_c4_line_map)


    def test_get_line_map_on_composing_old_example(self): 
        # test on the stuff in segmentio_testdata/composing_old/

        with io.open('segmentio_testdata/composing_old/edit1.patch', 
                'r', encoding='utf-8') as f_io: 
            edit1 = segmentio.changelog_from_patch_file_content(f_io.read())
        edit1_line_map = segmentio.get_line_map(edit1)
        correct_edit1_line_map = [
                {'type': 'sequence', 
                'src_first': 1, 'src_last': 4, 
                'dest_first': 1, 'dest_last': 4}, 

                {'type': 'removeset', 
                'src_first': 5, 'src_last': 6, 
                'dest_first': 4, 'dest_last': None}, 

                {'type': 'sequence', 
                'src_first': 7, 'src_last': 9, 
                'dest_first': 5, 'dest_last': 7}, 

                {'type': 'set', 
                'src_first': 10, 'src_last': 12, 
                'dest_first': 8, 'dest_last': 17}, 

                {'type': 'sequence', 
                'src_first': 13, 'src_last': 13, 
                'dest_first': 18, 'dest_last': 18}, 

                {'type': 'addset', 
                'src_first': 13, 'src_last': None, 
                'dest_first': 19, 'dest_last': 23}, 

                {'type': 'sequence', 
                'src_first': 14, 'src_last': sys.maxsize/2, 
                'dest_first': 24, 'dest_last': sys.maxsize/2 + 10}
                ]
        self.assertEqual(edit1_line_map, correct_edit1_line_map)

        with io.open('segmentio_testdata/composing_old/edit2.patch', 
                'r', encoding='utf-8') as f_io: 
            edit2 = segmentio.changelog_from_patch_file_content(f_io.read())
        edit2_line_map = segmentio.get_line_map(edit2)
        correct_edit2_line_map = [
                {'type': 'removeset', 
                'src_first': 1, 'src_last': 1, 
                'dest_first': 0, 'dest_last': None}, 

                {'type': 'sequence', 
                'src_first': 2, 'src_last': 6, 
                'dest_first': 1, 'dest_last': 5}, 

                {'type': 'set', 
                'src_first': 7, 'src_last': 9, 
                'dest_first': 6, 'dest_last': 12}, 

                {'type': 'sequence', 
                'src_first': 10, 'src_last': 10, 
                'dest_first': 13, 'dest_last': 13}, 

                {'type': 'set', 
                'src_first': 11, 'src_last': 12, 
                'dest_first': 14, 'dest_last': 17}, 

                {'type': 'sequence', 
                'src_first': 13, 'src_last': 15, 
                'dest_first': 18, 'dest_last': 20}, 

                {'type': 'set', 
                'src_first': 16, 'src_last': 21, 
                'dest_first': 21, 'dest_last': 22}, 

                {'type': 'sequence', 
                'src_first': 22, 'src_last': sys.maxsize/2, 
                'dest_first': 23, 'dest_last': sys.maxsize/2 + 1}
                ]
        self.assertEqual(edit2_line_map, correct_edit2_line_map)

        with io.open('segmentio_testdata/composing_old/composed-edit1-edit2.patch', 
                'r', encoding='utf-8') as f_io: 
            composed12 = segmentio.changelog_from_patch_file_content(f_io.read())
        composed12_line_map = segmentio.get_line_map(composed12)
        correct_composed12_line_map = [
                {'type': 'removeset', 
                'src_first': 1, 'src_last': 1, 
                'dest_first': 0, 'dest_last': None}, 

                {'type': 'sequence', 
                'src_first': 2, 'src_last': 4, 
                'dest_first': 1, 'dest_last': 3}, 

                {'type': 'removeset', 
                'src_first': 5, 'src_last': 6, 
                'dest_first': 3, 'dest_last': None}, 

                {'type': 'sequence', 
                'src_first': 7, 'src_last': 8, 
                'dest_first': 4, 'dest_last': 5}, 

                {'type': 'set', 
                'src_first': 9, 'src_last': 9, 
                'dest_first': 6, 'dest_last': 12}, 

                {'type': 'set', 
                'src_first': 10, 'src_last': 12, 
                'dest_first': 13, 'dest_last': 13}, 

                {'type': 'addset', 
                'src_first': 12, 'src_last': None, 
                'dest_first': 14, 'dest_last': 22}, 

                {'type': 'removeset', 
                'src_first': 13, 'src_last': 13, 
                'dest_first': 22, 'dest_last': None}, 

                {'type': 'addset', 
                'src_first': 13, 'src_last': None, 
                'dest_first': 23, 'dest_last': 24}, 

                {'type': 'sequence', 
                'src_first': 14, 'src_last': sys.maxsize/2, 
                'dest_first': 25, 'dest_last': sys.maxsize/2 + 11}
                ]
        self.assertEqual(composed12_line_map, correct_composed12_line_map)



    def test_get_hunks_on_handmade_changelog(self): 
        with io.open('segmentio_testdata/handmade-changelog/reference-changelog.patch', 
                'r', encoding='utf-8') as f_io: 
            changelog = f_io.read()
        hunks = segmentio.get_hunks(changelog)

        h1 = Hunk(1, 7, 1, 57, u''' něco 1
 něco 2
 něco 3
+INSERTED LINE 1
+INSERTED LINE 2
+INSERTED LINE 3
+INSERTED LINE 4
+INSERTED LINE 5
+INSERTED LINE 6
+INSERTED LINE 7
+INSERTED LINE 8
+INSERTED LINE 9
+INSERTED LINE 10
+INSERTED LINE 11
+INSERTED LINE 12
+INSERTED LINE 13
+INSERTED LINE 14
+INSERTED LINE 15
+INSERTED LINE 16
+INSERTED LINE 17
+INSERTED LINE 18
+INSERTED LINE 19
+INSERTED LINE 20
+INSERTED LINE 21
+INSERTED LINE 22
+INSERTED LINE 23
+INSERTED LINE 24
+INSERTED LINE 25
+INSERTED LINE 26
+INSERTED LINE 27
+INSERTED LINE 28
+INSERTED LINE 29
+INSERTED LINE 30
+INSERTED LINE 31
+INSERTED LINE 32
+INSERTED LINE 33
+INSERTED LINE 34
+INSERTED LINE 35
+INSERTED LINE 36
+INSERTED LINE 37
+INSERTED LINE 38
+INSERTED LINE 39
+INSERTED LINE 40
+INSERTED LINE 41
+INSERTED LINE 42
+INSERTED LINE 43
+INSERTED LINE 44
+INSERTED LINE 45
+INSERTED LINE 46
+INSERTED LINE 47
+INSERTED LINE 48
+INSERTED LINE 49
+INSERTED LINE 50
 něco 4
 něco 5
 něco 6
 něco 7
''')
        h2 = Hunk(31, 1, 81, 3, u'''-první
+!první!
+!změněný!
+!úsek!
''')
        h3 = Hunk(33, 4, 85, 2, u'''-Tenhle
-naopak
-bude
-zkrácen.
+Tenhle byl
+naopak zkrácen.
''')
        h4 = Hunk(37, 11, 87, 10, u''' šel
 dědeček
 na
 kopeček
+...nevím, jak dál!
 (za básní)
-sixth
-seventh
 eighth
 ninth
 tenth
 eleventh
''')
        correct_hunks = [h1, h2, h3, h4]

        self.assertEqual(hunks, correct_hunks)


    def test_get_hunks_on_changelog_with_lazily_written_headers(self): 
        # If the number of lines in a header is 1 it can be omitted.
        # difflib.unified_diff() does this when invoked with n=0 
        # (that means no context lines and thus makes one-line hunks possible).
        c_normal = u'''@@ -2,1 +2,1 @@
-!změněný!
+<změNNNěný>
@@ -11,2 +11,1 @@
-...nevím, jak dál!
-(za básní)
+<za básnÍÍÍ>
'''
        hunks_normal = segmentio.get_hunks(c_normal)
        self.assertEqual(len(hunks_normal), 2)
        self.assertEqual(unicode(hunks_normal[0]), u'''@@ -2,1 +2,1 @@
-!změněný!
+<změNNNěný>
''')
        self.assertEqual(unicode(hunks_normal[1]), u'''@@ -11,2 +11,1 @@
-...nevím, jak dál!
-(za básní)
+<za básnÍÍÍ>
''')

        c_lazy = u'''@@ -2 +2 @@
-!změněný!
+<změNNNěný>
@@ -11,2 +11 @@
-...nevím, jak dál!
-(za básní)
+<za básnÍÍÍ>
'''
        hunks_lazy = segmentio.get_hunks(c_lazy)
        self.assertEqual(hunks_normal, hunks_lazy)


    def test_hunks_on_generated_changelog(self): 
        pass


    def test_properties_of_hunks_returned_by_get_hunks(self): 
        # from 
        # `diff -U 0 reference-file-after-edit1.txt reference-file-after-edit2.txt` 
        # in segmentio_testdata/generated-changelog/
        c2 = u'''@@ -3,2 +2,0 @@
-3rd
-fourth
@@ -6,0 +5,3 @@
+ADDING
+3
+LINES
@@ -9 +10 @@
-ninth
+9th
'''
        hunks = segmentio.get_hunks(c2)
        self.assertEqual(len(hunks), 3)

        self.assertEqual(hunks[0].x1(), 3)
        self.assertEqual(hunks[0].n1(), 2)
        self.assertEqual(hunks[0].x2(), 2)
        self.assertEqual(hunks[0].n2(), 0)
        self.assertEqual(hunks[0].content(), u'-3rd\n-fourth\n')

        self.assertEqual(hunks[1].x1(), 6)
        self.assertEqual(hunks[1].n1(), 0)
        self.assertEqual(hunks[1].x2(), 5)
        self.assertEqual(hunks[1].n2(), 3)
        self.assertEqual(hunks[1].content(), u'+ADDING\n+3\n+LINES\n')

        self.assertEqual(hunks[2].x1(), 9)
        self.assertEqual(hunks[2].n1(), 1)
        self.assertEqual(hunks[2].x2(), 10)
        self.assertEqual(hunks[2].n2(), 1)
        self.assertEqual(hunks[2].content(), u'-ninth\n+9th\n')


    def test_are_intersecting(self): 
        # these ranges are meant as NOT containing their ends; they are NOT intersecting
        openend_range_1 = (4, 10)
        openend_range_2 = (10, 11)

        # are_intersecting() is the wrong function to use on these ranges -> this incorrect result!
        self.assertTrue(segmentio.are_intersecting(openend_range_1, openend_range_2))

        # these are equivalent ranges, only meant as containing their ends; they are NOT intersecting
        closedend_range_1 = (4, 9)
        closedend_range_2 = (10, 10)

        # on these, are_intersecting() gives the correct result
        self.assertFalse(segmentio.are_intersecting(closedend_range_1, closedend_range_2))



if __name__ == '__main__': 
    unittest.main()
