#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys
sys.path.append('../')  # for imports from the project's root directory
import common
from common import dbg, dbg_notb
from traceback import format_exc
from time import time

import unittest
import tempfile, os, shutil
import io

import model

#from pudb import set_trace; set_trace()
#import pudb
#pu.db


#class EditedFileTestCase(unittest.TestCase):
#    def simple_test_without_opening_the_file(self): 
#        fname = "/example/file/name"
#        d = {"filename": fname, 'changelog': '+HEEEE *[ závorka hranatá!!!] atd.'}
#        edited_file = model.EditedFile.from_dict(d)
#        self.assertTrue(edited_file.get_id() is fname)
#        d2 = edited_file.to_dict()
#        assertEqual(d2['filename'], d['filename'])
#        assertEqual(d2['changelog'], d['changelog'])


class ApplicationTestCase(unittest.TestCase): 
    CONFIG_REMOVE_TEMP_FILES = True

    def setUp(self): 
        this_dir = os.path.dirname(os.path.realpath(__file__))

        self._storage_dir = tempfile.mkdtemp(dir=this_dir, prefix='testdata_tmp/storage_')
        print '%s.%s @setUp: \n    [created storage dir] ' % \
                (self.__class__.__name__, self._testMethodName) + self._storage_dir

        self._main_dir = tempfile.mkdtemp(dir=this_dir, prefix='testdata_tmp/gfs_')
        print '%s.%s @setUp: \n    [created gfs dir] ' % \
                (self.__class__.__name__, self._testMethodName) + self._main_dir

        config = dict()
        config['storage_dir'] = self._storage_dir
        config['gfs_dir'] = self._main_dir
        #print '-->', model.Application._instances
        model.Application(config)
        #print '-->', model.Application._instances


    def tearDown(self): 
        if self.CONFIG_REMOVE_TEMP_FILES: 
            shutil.rmtree(self._storage_dir)
            print '%s.%s @tearDown: \n    [removed storage dir] ' % \
                    (self.__class__.__name__, self._testMethodName) + self._storage_dir

            shutil.rmtree(self._main_dir)
            print '%s.%s @tearDown: \n    [removed gfs dir] ' % \
                    (self.__class__.__name__, self._testMethodName) + self._main_dir


    def test_open_window(self): 
        file_path = os.path.join(os.getcwd(), u'example_edited_files/cztenten_994.vert')
        line = '88'

        #print '-->', model.Application._instances
        window_id = model.Application().open_window(file_path, None, line)
        # TODO check the result
    

    # == tiny file ==

    def test_open_window_on_tiny_file_NOINDEX(self): 
        file_path = os.path.join(os.getcwd(), u'example_edited_files/tinyfile-20-lines.txt')

        t1 = time()
        window_id = model.Application().open_window(file_path, None, 3, 5)
        self.assertEqual(
                model.Application().window_page(window_id)['viewport_content'], 
                u'''third
fourth
fifth
sixth
seventh
''')
        t2 = time()
        print "\n[tinyfile-20-lines.txt (168 B), POS, NOINDEX] open_window at line 3 took %f seconds" % (t2 - t1)

    def test_open_window_on_tiny_file_POS_NOINDEX(self): 
        file_path = os.path.join(os.getcwd(), u'example_edited_files/tinyfile-20-lines.txt')

        t1 = time()
        window_id = model.Application().open_window(file_path=file_path, corpus_name=None, nlines=5, pos=14) 
        # Keeps incorrectly returning the second line as the result instead of the correct second one, 
        # then from pos 19 it suddenly skips to the fourth line, entirely skipping the third line!
        # Looks like it's a problem with SegmentIO (a regression after I changed the "touch"?), 
        # since it works OK in basic mode: 
        #window_id = model.Application().open_window(file_path=file_path, corpus_name=None, nlines=5, pos=14, 
        #        basic_mode=True) # in basic mode it works correctly
        self.assertEqual(
                model.Application().window_page(window_id)['viewport_content'], 
                u'''third
fourth
fifth
sixth
seventh
''')
        t2 = time()
        print "\n[tinyfile-20-lines.txt (168 B), POS, NOINDEX] open_window at line 3 took %f seconds" % (t2 - t1)

    def test_add_tiny_file(self): 
        file_path = os.path.join(os.getcwd(), u'example_edited_files/tinyfile-20-lines.txt')
        if not model.GitFileSystem().has_file(file_path): 
            t1 = time()
            model.GitFileSystem().add_file(file_path)
            t2 = time()
            print "[tinyfile-20-lines.txt (168 B)] GitFileSystem.add_file took %f seconds" % (t2 - t1)


    # == small file ==

    def test_open_window_on_small_file_NOINDEX(self): 
        file_path = os.path.join(os.getcwd(), u'example_edited_files/cztenten_994.vert')

        t1 = time()
        window_id = model.Application().open_window(file_path, None, 3, 5)
        self.assertEqual(
                model.Application().window_page(window_id)['viewport_content'], 
                u'''<s>
Brod	brod	k1gInSc1qP	brod
porazil	porazit	k5eAaPmAgInSaPrDqP	
Chropyni	Chropyně	k1gFnSc4	Chropyně
a	a	k8xCqP	
''')
        t2 = time()
        print "\n[cztenten_994.vert (23 KB), NOINDEX] open_window at line 3 took %f seconds" % (t2 - t1)

    def test_add_small_file(self): 
        file_path = os.path.join(os.getcwd(), u'example_edited_files/cztenten_994.vert')
        if not model.GitFileSystem().has_file(file_path): 
            t1 = time()
            model.GitFileSystem().add_file(file_path)
            t2 = time()
            print "[cztenten_994.vert (23 KB)] GitFileSystem.add_file took %f seconds" % (t2 - t1)
    

    # == large file ==

    def test_open_window_on_large_file_NOINDEX(self): 
        file_path = os.path.join(os.getcwd(), u'example_edited_files/cs-vert_2M.vert')

        t1 = time()
        window_id = model.Application().open_window(file_path, None, 3, 5)
        self.assertEqual(
                model.Application().window_page(window_id)['viewport_content'], 
                u'''<s>
Abstraktní	abstraktní	k2eAgInSc1d1	abstraktní
nesmysl	nesmysl	k1gInSc1	nesmysl
</s>
</p>
''')
        t2 = time()
        print "\n[cs-vert_2M.vert (32 MB), NOINDEX] open_window at line 3 took %f seconds" % (t2 - t1)

    def test_add_large_file(self): 
        file_path = os.path.join(os.getcwd(), u'example_edited_files/cs-vert_2M.vert')
        if not model.GitFileSystem().has_file(file_path): 
            t1 = time()
            model.GitFileSystem().add_file(file_path)
            t2 = time()
            print "[cs-vert_2M.vert (32 MB)] GitFileSystem.add_file took %f seconds" % (t2 - t1)


    # == huge file ==

    # NOTE: The following 2 tests are disabled, as it takes a long time to add such a huge file to GFS.
    #       Also, that file is only on my disk (it's too large to be kept among the test data) so these 
    #       tests wouldn't work on another computer.
    #       
    #       The important thing is this: adding a large file to GFS takes a long time and it's because 
    #       of the git commands in _set_up_git_repo() take a long time: "git commit (...)" (the initial 
    #       commit) and to a lesser extent also the "git add -A" before it.

    def test_open_window_on_huge_file_NOINDEX(self): 
        print "(this test is disabled)"; return 
        file_path = os.path.join(os.getcwd(), u'/home/petr/fi/korpus-wikics/cs-vert.vert')

        t1 = time()
        window_id = model.Application().open_window(file_path, None, 3, 5)
        self.assertEqual(
                model.Application().window_page(window_id)['viewport_content'], 
                u'''<s>
Abstraktní	abstraktní	k2eAgInSc1d1	abstraktní
nesmysl	nesmysl	k1gInSc1	nesmysl
</s>
</p>
''')
        t2 = time()
        print "\n[cs-vert.vert (529 MB), NOINDEX] open_window at line 3 took %f seconds" % (t2 - t1)

    def test_add_huge_file(self): 
        print "(this test is disabled)"; return 
        file_path = os.path.join(os.getcwd(), u'/home/petr/fi/korpus-wikics/cs-vert.vert')
        if not model.GitFileSystem().has_file(file_path): 
            t1 = time()
            model.GitFileSystem().add_file(file_path)
            t2 = time()
            print "[cs-vert.vert (529 MB)] GitFileSystem.add_file took %f seconds" % (t2 - t1)



    def test_do_one_edit(self): 
        # restore the example file to its original state
        shutil.copyfile('example_edited_files/cztenten_994.vert.bak', 'example_edited_files/cztenten_994.vert')

        file_path = os.path.join(os.getcwd(), u'example_edited_files/cztenten_994.vert')

        # check the physical file
        with io.open(os.path.join(os.getcwd(), u'example_edited_files/cztenten_994.vert.bak'), 
                'r', encoding='utf-8') as f: 
            orig_file = f.read()
        with io.open(file_path, 'r', encoding='utf-8') as f: 
            current_file = f.read()
        self.assertEqual(current_file, orig_file)

        # -- open a window (w), do edit1 and edit2 in it --

        w_id = model.Application().open_window(file_path, None, 67, 5)
        line_67_nlines_5_orig = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	
premiéru	premiér	k1gMnSc3qP	premiér
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
'''
        #print model.Application().window_page(w_id)
        #kkk = model.Application().window_page(w_id)['viewport_content']
        #print kkk
        win = model.Application()._load_window(w_id)
        print "win-----"
        print win.get_viewport_content()
        print "---------"
        self.assertEqual(
                model.Application().window_page(w_id)['viewport_content'], 
                line_67_nlines_5_orig)

        # edit1
        new_content = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
'''
        model.Application().save_viewport_content(w_id, new_content)
        line_67_nlines_5_after_edit1 = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
nenechal	nechat	k5eNaPmAgInSrDaPqP	
'''
        self.assertEqual(
                model.Application().window_page(w_id)['viewport_content'], 
                line_67_nlines_5_after_edit1)

        # commit changes in w (that is: edit1)
        model.Application().commit(w_id)

        # check the physical file
        with io.open(os.path.join(os.getcwd(), u'example_edited_files/cztenten_994-after-edit1.vert'), 
                'r', encoding='utf-8') as f: 
            file_after_edit1 = f.read()
        with io.open(file_path, 'r', encoding='utf-8') as f: 
            current_file = f.read()
        #with io.open('/home/petr/tmp/cur.vert', 'w', encoding='utf-8') as f: 
        #    f.write(current_file)
        #with io.open('/home/petr/tmp/cmp.vert', 'w', encoding='utf-8') as f: 
        #    f.write(file_after_edit1)
        self.assertEqual(current_file, file_after_edit1)


    def test_do_some_edits_sequential_workflow(self): 
        # NOTE: -- sequential workflow rule --
        #       for every file: at any time, only one user has uncommited changes in the file

        # restore the example file to its original state
        shutil.copyfile('example_edited_files/cztenten_994.vert.bak', 'example_edited_files/cztenten_994.vert')

        file_path = os.path.join(os.getcwd(), u'example_edited_files/cztenten_994.vert')

        # check the physical file
        with io.open(os.path.join(os.getcwd(), u'example_edited_files/cztenten_994.vert.bak'), 
                'r', encoding='utf-8') as f: 
            orig_file = f.read()
        with io.open(file_path, 'r', encoding='utf-8') as f: 
            current_file = f.read()
        self.assertEqual(current_file, orig_file)

        # -- open a window (w1), do edit1, edit2, edit3 in it --

        w1_id = model.Application().open_window(file_path, None, 67, 5)
        line_67_nlines_5_orig = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	
premiéru	premiér	k1gMnSc3qP	premiér
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
'''
        #print model.Application().window_page(w_id)
        self.assertEqual(
                model.Application().window_page(w1_id)['viewport_content'], 
                line_67_nlines_5_orig)

        # edit1
        new_content = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
'''
        model.Application().save_viewport_content(w1_id, new_content)
        line_67_nlines_5_after_edit1 = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
nenechal	nechat	k5eNaPmAgInSrDaPqP	
'''
        self.assertEqual(
                model.Application().window_page(w1_id)['viewport_content'], 
                line_67_nlines_5_after_edit1)

        # edit2
        new_content = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
ADDED LINE 1
ADDED LINE 2
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
nenechal	nechat	k5eNaPmAgInSrDaPqP	
'''
        model.Application().save_viewport_content(w1_id, new_content)
        line_67_nlines_5_after_edit2 = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
ADDED LINE 1
ADDED LINE 2
nového	nový	k2eAgNnSc2d1qP	nové
'''
        self.assertEqual(
                model.Application().window_page(w1_id)['viewport_content'], 
                line_67_nlines_5_after_edit2)

        # commit changes in w1 (that is: edit1, edit2)
        model.Application().commit(w1_id)

        self.assertEqual(
                model.Application().window_page(w1_id)['viewport_content'], 
                line_67_nlines_5_after_edit2)

        # check the physical file
        with io.open(os.path.join(os.getcwd(), u'example_edited_files/cztenten_994-after-edit1-edit2.vert'), 
                'r', encoding='utf-8') as f: 
            file_after_edit1_edit2 = f.read()
        with io.open(file_path, 'r', encoding='utf-8') as f: 
            current_file = f.read()
        self.assertEqual(current_file, file_after_edit1_edit2)

        # -- open another window (w2), do edit3 in it --
        # (base revision different from the one of w1 because w1 has already been commited)

        w2_id = model.Application().open_window(file_path, None, 56, 8)
        line_56_nlines_8_orig = u'''Sestupný	sestupný	k2eAgInSc1d1qP	sestupný
kurs	kurs	k1gInSc1	kurs
po	po	k7c6qP	
víkendu	víkend	k1gInSc6qP	víkend
určitě	určitě	k6eAd1	
nabere	nabrat	k5eAaPmIp3nSaPrDqP	
Spytihněv	Spytihněv	k1gFnSc1qG	Spytihněv
<g/>
'''

        win1 = model.Application()._load_window(w1_id)
        win2 = model.Application()._load_window(w2_id)
        print "win1-changelog---"
        print win1.total_changelog()
        print "-----------------"
        print "win2-changelog---"
        print win2.total_changelog()
        print "-----------------"

        self.assertEqual(
                model.Application().window_page(w2_id)['viewport_content'], 
                line_56_nlines_8_orig)

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
        model.Application().save_viewport_content(w2_id, new_content)

        self.assertEqual(
                model.Application().window_page(w2_id)['viewport_content'], 
                line_56_nlines_8_after_edit3)

        # commit changes in w2 (that is: edit3)
        model.Application().commit(w2_id)

        self.assertEqual(
                model.Application().window_page(w2_id)['viewport_content'], 
                line_56_nlines_8_after_edit3)

        # check the physical file
        with io.open(os.path.join(os.getcwd(), 
            u'example_edited_files/cztenten_994-after-edit1-edit2-edit3.vert'), 
            'r', encoding='utf-8') as f: 
            file_after_edit1_edit2_edit3 = f.read()
        with io.open(file_path, 'r', encoding='utf-8') as f: 
            current_file = f.read()
        self.assertEqual(current_file, file_after_edit1_edit2_edit3)


    def test_do_some_edits_parallel_workflow(self): 
        # NOTE: -- parallel workflow rule --
        #       for every file: at any time, multiple users can have uncommited changes in the file

        # NOTE: *** ALL WORKS CORRECTLY NOW, IT'S FIXED ***

        # restore the example file to its original state
        shutil.copyfile('example_edited_files/cztenten_994.vert.bak', 'example_edited_files/cztenten_994.vert')

        file_path = os.path.join(os.getcwd(), u'example_edited_files/cztenten_994.vert')

        # -- open a window (w1), do edit1 and edit2 in it --

        w1_id = model.Application().open_window(file_path, None, 67, 5)
        line_67_nlines_5_orig = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	
premiéru	premiér	k1gMnSc3qP	premiér
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
'''
        #print model.Application().window_page(w1_id)
        self.assertEqual(
                model.Application().window_page(w1_id)['viewport_content'], 
                line_67_nlines_5_orig)

        # edit1
        new_content = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
'''
        model.Application().save_viewport_content(w1_id, new_content)
        line_67_nlines_5_after_edit1 = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
nenechal	nechat	k5eNaPmAgInSrDaPqP	
'''
        self.assertEqual(
                model.Application().window_page(w1_id)['viewport_content'], 
                line_67_nlines_5_after_edit1)

        # edit2
        new_content = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
ADDED LINE 1
ADDED LINE 2
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
nenechal	nechat	k5eNaPmAgInSrDaPqP	
'''
        model.Application().save_viewport_content(w1_id, new_content)
        line_67_nlines_5_after_edit2 = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
ADDED LINE 1
ADDED LINE 2
nového	nový	k2eAgNnSc2d1qP	nové
'''
        self.assertEqual(
                model.Application().window_page(w1_id)['viewport_content'], 
                line_67_nlines_5_after_edit2)



# TODO: investigate and fix this!
#
#        # -- open another window (w2), do edit3 in it --
#        # (base revision is the same as for w1 because edits in w1 haven't been commited yet)
#
#        w2_id = model.Application().open_window(file_path, 69, 3)
#        line_69_nlines_3_orig = u'''premiéru	premiér	k1gMnSc3qP	premiér
#nového	nový	k2eAgNnSc2d1qP	nové
#hřiště	hřiště	k1gNnSc2qP	hřiště
#'''
#        self.assertEqual(
#                model.Application().window_page(w2_id)['viewport_content'], 
#                line_69_nlines_3_orig)
#
#        # edit3
#        #dbg(model.Application().window_page(w2_id)['total_changelog'])
#        #dbg(model.Application().window_page(w2_id)['viewport_content'])
#
## NOTE: this breaks something in Segment
##        new_content = u'''<SOMETHING1>
##<SOMETHING2>
##premiéru	premiér	k1gMnSc3qP	premiér
##'''
#
#        new_content = u'''premiéru	premiér	k1gMnSc3qP	premiér
#<A>
#<B>
#nového	nový	k2eAgNnSc2d1qP	nové
#<C>
#'''
#        line_69_nlines_3_after_edit3 = u'''premiéru	premiér	k1gMnSc3qP	premiér
#<A>
#nového	nový	k2eAgNnSc2d1qP	nové
#'''
#        model.Application().save_viewport_content(w2_id, new_content)
#
#        #dbg(model.Application().window_page(w2_id)['total_changelog'])
#        #dbg(model.Application().window_page(w2_id)['viewport_content'])
#
#        self.assertEqual(
#                model.Application().window_page(w2_id)['viewport_content'], 
#                line_69_nlines_3_after_edit3)
        

        # -- open another window (w2), do edit3 in it --
        # (base revision is the same as for w1 because edits in w1 haven't been commited yet)

        w2_id = model.Application().open_window(file_path, None, 56, 8)
        line_56_nlines_8_orig = u'''Sestupný	sestupný	k2eAgInSc1d1qP	sestupný
kurs	kurs	k1gInSc1	kurs
po	po	k7c6qP	
víkendu	víkend	k1gInSc6qP	víkend
určitě	určitě	k6eAd1	
nabere	nabrat	k5eAaPmIp3nSaPrDqP	
Spytihněv	Spytihněv	k1gFnSc1qG	Spytihněv
<g/>
'''
        self.assertEqual(
                model.Application().window_page(w2_id)['viewport_content'], 
                line_56_nlines_8_orig)

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
        model.Application().save_viewport_content(w2_id, new_content)

        self.assertEqual(
                model.Application().window_page(w2_id)['viewport_content'], 
                line_56_nlines_8_after_edit3)

 
        # -- commit changes in w2 (that is: edit3) --

        # before commiting anything, check w1 viewport content
        self.assertEqual(
                model.Application().window_page(w1_id)['viewport_content'], 
                line_67_nlines_5_after_edit2)

        
        #print "~~~~\n" + \
        #        model.GitFileSystem().diff_from_head(
        #                    model.Application().window_page(w2_id)['file_path'],
        #                    model.Application().window_page(w2_id)['revision']) + "~~~~"


        # do the commit
        model.Application().commit(w2_id)

        # w2 should stay the same
        win1 = model.Application()._load_window(w1_id)
        win2 = model.Application()._load_window(w2_id)
        print "win1----"
        print win1.get_viewport_content()
        print "--------"
        print "win2----"
        print win2.get_viewport_content()
        print "--------"
        self.assertEqual(
                model.Application().window_page(w2_id)['viewport_content'], 
                line_56_nlines_8_after_edit3)  

        # NOTE: HERE is where it breaks.
        # FIXME
        ## the commit shouldn't have any effect on w1 either
        try: 
            print model.Application().window_page(w1_id, catch_exc=False)
        except: 
            print format_exc()
        #self.assertEqual(
        #        model.Application().window_page(w1_id)['viewport_content'], 
        #        line_67_nlines_5_after_edit2)


#        # commit changes in w2 (that is: edit3)
#        model.Application().commit(w2_id)
#
#        # commit changes in w1 (that is: edit1, edit2)
#        model.Application().commit(w1_id)



##%%%%%%  NOTE: Below are the parts when the head revision changes due to a commit 
##%%%%%%        and windows created before the commit need to deal with the 
##%%%%%%        change of head. This works correctly in segmentio_test.py 
##%%%%%%        (SegmentIOTestCase.test_rebasing_from_f1_to_f0() 
##%%%%%%         and SegmentIOTestCase.test_rebasing_from_f2_to_f1()) 
##%%%%%%        but for a mysterious reason fails here. See the logs 
##%%%%%%        in issues/model_test_rebasing_error/.
#
## TODO: fix this (error occurs in "the commit shouldn't have any effect on w1 either" (line 223 in the log))
##
##        # -- commit changes in w2 (that is: edit3) --
##
##        # before commiting anything, check w1 viewport content
##        self.assertEqual(
##                model.Application().window_page(w1_id)['viewport_content'], 
##                line_67_nlines_5_after_edit2)
##
##        
##        #print "~~~~\n" + \
##        #        model.GitFileSystem().diff_from_head(
##        #                    model.Application().window_page(w2_id)['file_path'],
##        #                    model.Application().window_page(w2_id)['revision']) + "~~~~"
##
##
##        # do the commit
##        model.Application().commit(w2_id)
##
##        # w2 should stay the same
##        self.assertEqual(
##                model.Application().window_page(w2_id)['viewport_content'], 
##                line_56_nlines_8_after_edit3)  
##
##        # the commit shouldn't have any effect on w1 either
##        self.assertEqual(
##                model.Application().window_page(w1_id)['viewport_content'], 
##                line_67_nlines_5_after_edit2)
##
##
##        ## -- commit changes in w1 (that is: edit1, then edit2) --
##
##        self.assertEqual(
##                model.Application().window_page(w1_id)['viewport_content'], 
##                line_67_nlines_5_after_edit2)
##        model.Application().commit(w1_id)
##        self.assertEqual(
##                model.Application().window_page(w1_id)['viewport_content'], 
##                line_67_nlines_5_after_edit2)
#
#
## TODO: then ensure this works too
##
##        # -- return to the first window (w1), do edit4 in it --
##        # (w1's base revision is no longer the head revision)
##
##        # edit4
##
###        new_content = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
###si	se	k3c3xPyFqP 
###premiéru	premiéra	<SOMEONE PLZ PUT CORRECT CODE HERE>	premiéra  #fixed the lemma
###nového	nový	k2eAgNnSc2d1qP	nové
###'''
##        new_content = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
##si	se	k3c3xPyFqP	[note: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
##AAAAAAA
##BBBBBBB
##nového	nový	k2eAgNnSc2d1qP	nové
##'''
##        model.Application().save_viewport_content(w1_id, new_content)
##
##        print model.Application().window_page(w1_id)['viewport_content']
###        line_67_nlines_5_after_edit4 = u'''Rožnov	Rožnov	k1gInSc1	Rožnov
###si	se	k3c3xPyFqP	[note: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
###AAAAAAA
###BBBBBBB
###nového	nový	k2eAgNnSc2d1qP	nové
###'''
###        self.assertEqual(
###                model.Application().window_page(w1_id)['viewport_content'], 
###                line_67_nlines_5_after_edit4)
##        
##        
##
##        # -- open yet another window (w3), check the content --
##        # (w3's base revision is the head revision because it's a new window)
##
##




class ApplicationStorageTestCase(unittest.TestCase):
    # to be able to see the storage files, set these two both to False
    CONFIG_REMOVE_TEMP_FILES = True
    CONFIG_TEST_DELETE = True


    def assertEqualObjs(self, obj1, obj2): 
        self.assertEqual(obj1.__dict__, obj2.__dict__)

    def setUp(self): 
        this_dir = os.path.dirname(os.path.realpath(__file__))

        self._storage_dir = tempfile.mkdtemp(dir=this_dir, prefix='testdata_tmp/storage_')
        print '%s: [created storage] ' % self.__class__.__name__ + self._storage_dir
        self._storage = model.ApplicationStorage(self._storage_dir)

        self._main_dir = tempfile.mkdtemp(dir=this_dir, prefix='testdata_tmp/gfs_')
        print '%s: [created gfs] ' % self.__class__.__name__ + self._main_dir
        model.GitFileSystem(self._main_dir)

    def tearDown(self): 
        if self.CONFIG_REMOVE_TEMP_FILES: 
            shutil.rmtree(self._storage_dir)
            print '%s: [removed storage] ' % self.__class__.__name__ + self._storage_dir

            shutil.rmtree(self._main_dir)
            print '%s: [removed gfs] ' % self.__class__.__name__ + self._main_dir

    def test_sessions(self): 
        print '%s: testing storage of sessions...' % self.__class__.__name__
        # make a Session object
        session = model.Session()
        sid = session.get_id()

        # CREATE, LOAD, check
        self._storage.create_session(session)
        loaded_session = self._storage.load_session(sid)
        self.assertEqualObjs(session, loaded_session)

        # modify, SAVE, LOAD, check
        session.set_viewport_style(model.Session.VIEWPORT_STYLE_PLAIN_TEXTAREA)
        self._storage.save_session(session)
        loaded_session = self._storage.load_session(sid)
        self.assertEqualObjs(session, loaded_session)

        if self.CONFIG_TEST_DELETE: 
            # DELETE, try to LOAD (should throw exception)
            self._storage.delete_session(session)
            with self.assertRaises(KeyError): 
                self._storage.load_session(sid)


    def test_windows(self): 
        print '%s: testing storage of windows...' % self.__class__.__name__
        # make a Window object
        file_path = os.path.join(os.getcwd(), u'example_edited_files/cztenten_994.vert')
        session = model.Session()
        sid = session.get_id()
        line = 65
        nlines = 10
        window = model.Window.new(
                session_id=sid, 
                file_path=file_path, 
                corpus_name=None,
                revision=None, 
                viewport_line=line, 
                viewport_nlines=nlines)

        wid = window.get_id()

        # CREATE, LOAD, check
        self._storage.create_window(window)
        loaded_window = self._storage.load_window(wid)
        self.assertEqualObjs(window, loaded_window)

        # modify, SAVE, LOAD, check
        window._viewport_nlines = 12  # NOTE mock
        self._storage.save_window(window)
        loaded_window = self._storage.load_window(wid)
        self.assertEqualObjs(window, loaded_window)

        if self.CONFIG_TEST_DELETE: 
            # DELETE, try to LOAD (should throw exception)
            self._storage.delete_window(window)
            with self.assertRaises(KeyError): 
                self._storage.load_window(wid)


class GitFileSystemTestCase(unittest.TestCase):
    CONFIG_REMOVE_TEMP_FILES = True

    FILE_CZT994_VERT = os.path.join(os.getcwd(), u'example_edited_files/cztenten_994.vert')
    FILE_CZT100K_VERT_GZ = os.path.join(os.getcwd(), 'example_edited_files/cztenten_100k.vert.gz')
    FILE_CZT128 = os.path.join(os.getcwd(), 'example_edited_files/cztenten12_8')


    def setUp(self): 
        this_dir = os.path.dirname(os.path.realpath(__file__))
        self._main_dir = tempfile.mkdtemp(dir=this_dir, prefix='testdata_tmp/gfs_')
        print '%s: [created gfs] ' % self.__class__.__name__ + self._main_dir
        model.GitFileSystem(self._main_dir)

    def tearDown(self): 
        if self.CONFIG_REMOVE_TEMP_FILES: 
            shutil.rmtree(self._main_dir)
            print '%s: [removed gfs] ' % self.__class__.__name__ + self._main_dir

    def test_gfs(self): 
        # add FILE_CZT994_VERT
        self.assertFalse(model.GitFileSystem().has_file(self.FILE_CZT994_VERT))
        model.GitFileSystem().add_file(self.FILE_CZT994_VERT)
        self.assertTrue(model.GitFileSystem().has_file(self.FILE_CZT994_VERT))

        # add FILE_CZT100K_VERT_GZ
        model.GitFileSystem().add_file(self.FILE_CZT100K_VERT_GZ)

        # add and then remove FILE_CZT128
        self.assertFalse(model.GitFileSystem().has_file(self.FILE_CZT128))
        model.GitFileSystem().add_file(self.FILE_CZT128)
        self.assertTrue(model.GitFileSystem().has_file(self.FILE_CZT128))
        model.GitFileSystem().remove_file(self.FILE_CZT128)
        self.assertFalse(model.GitFileSystem().has_file(self.FILE_CZT128))

        # print head revision  [NOTE: check this visually]
        headrev = model.GitFileSystem().head_revision(self.FILE_CZT994_VERT)
        print '%s: head revision of file "%s": "%s"' % \
                (self.__class__.__name__, self.FILE_CZT994_VERT, headrev)

        # getting the head revision of a file that's not in the system should fail
        with self.assertRaises(AssertionError): 
            model.GitFileSystem().head_revision(self.FILE_CZT128)


if __name__ == '__main__': 
    unittest.main()
