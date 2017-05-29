#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys
sys.path.append('../')  # for imports from the project's root directory
import common
from common import dbg, get_dbg, dbg_notb, subprocess_call, LOG_FILE, SUBPROCESS_LOG_FILE
from traceback import format_exc

import idgen
from singleton import Singleton

#from jsonstorage import JSONStorage
from picklestorage import PickleStorage
import string
import json

from md5 import md5
import os
import shutil
import subprocess

import io
import segmentio

import lockdir


class Application(Singleton):
    def __init__(self, config=None, session_id=None): 
        if config is None: 
            # constructor called without args (just getting an instance; see Singleton)
            if self.__class__._instances is None: 
                # getting an instance but the singleton doesn't exist yet -> error: 
                raise Exception('error: cannot get an instance of Application the instance does not exist yet')
            else: 
                # getting an instance, the singleton instance exists already -> OK, 
                # __init__() doesn't do anything in this case
                return 

        #print "__init__ called"
        self._storage = ApplicationStorage(config['storage_dir'])
        #self._allowed_repository_paths = config['allowed_repository_paths']

        self._new_session_id = None
        #self._storage.get_lock()
        if session_id is None: 
            # the client did not provide a session ID -> create a new session
            s = Session(None)
            self._storage.create_session(s)
            self._session = s
            self._new_session_id = s.get_id()
        else: 
            # security check on the string provided as session ID
            #if not idgen.is_id(session_id): 
            #    raise Exception('session_id is badly formed')
            # NOTE: turned off this security check to allow users to make their own session IDs 
            #       (the 'username' URL parameter)

            # load the session 
            try:
                self._session = self._storage.load_session(session_id)
            except KeyError: 
                # we don't have a session with that ID -> create it
                s = Session(session_id)
                self._storage.create_session(s)
                self._session = s
                #self._new_session_id = s.get_id()
        #self._storage.release_lock()

        dbg("###incoming session_id: ", session_id, ", id of the actual Session: ", self._session.get_id())

        self._gfs = GitFileSystem(config['gfs_dir'], self._session.get_id())


    def close(self): 
        # close the storage (releases the locks)
        self._storage.close()




    def open_window(self, file_path=None, corpus_name=None, line=None, nlines=None, basic_mode=False, pos=None):
        assert file_path is None and corpus_name is not None or \
                corpus_name is None and file_path is not None

        assert pos != None or line != None
        assert not (pos != None and line != None)

        if corpus_name is not None: 
            file_path = self._file_path_for_corpus(corpus_name)
        #self._storage.get_lock()

        # create a new window on the file
        window = Window.new(
                session_id=self._session.get_id(), 
                file_path=file_path, 
                corpus_name=corpus_name, 
                revision=None,  # use the head revision as the physical file
                viewport_line=line, 
                viewport_nlines=(self._session.default_viewport_nlines() if nlines is None else nlines), 
                basic_mode=basic_mode, 
                pos=pos)

        self._storage.create_window(window)

        # register the window in the session 
        self._session.register_window(window.get_id())
        self._storage.save_session(self._session)

        #self._storage.release_lock()

        return window.get_id()

    
    def _complete_page_data(self, data): 
        data['session_id'] = self._session.get_id()
        #if self._new_session_id is not None: 
        #    # a new session has been started, set new_session_id so that the client 
        #    # stores its session ID in cookies
        #    data['new_session_id'] = self._new_session_id
        #    assert data['new_session_id'] == data['session_id']

        return data
    
    def _load_window(self, window_id): 
        # NOTE: use this to load a window of this user
        if window_id in self._session.window_ids():
            window = self._storage.load_window(window_id)
        else: 
            raise Exception("no window with id %s in session %s" % (window_id, self._session.get_id()))

        return window

    def _error_page_data(self, exception): 
        data = {'page_type': 'error', 'error_text': get_dbg(format_exc())}   #unicode(exception)
        return data

    def _error_ajax_data(self, exception): 
        error_text = get_dbg(unicode(exception))
        data = json.dumps({
            'viewport_line': 0, 
            'viewport_content': error_text, 
            'file_changelog': "---", 
            'status': '[AJAX: an error has occured]'})
        return data

    def home_page(self): 
        windows = []
        for window_id in self._session.window_ids(): 
            window = self._load_window(window_id)
            item = {'window_id': window_id, 
                    'file_path': window.file_path(), 
                    'corpus_name': window.corpus_name(), 
                    'viewport_line': window.viewport_line()}
            windows.append(item)

        files = self._gfs.all_files()

        return self._complete_page_data({'page_type': 'home', 'title': 'corpedit', 
            'windows': windows, 'files': files})

    def admin_page(self, msg=u''): 
        data = {'page_type': 'admin', 'msg': msg}
        return self._complete_page_data(data)

    def _clear_dir(self, dir_path): 
        dir_items = os.listdir(dir_path)
        for item in dir_items: 
            item_path = os.path.join(dir_path, item)
            shutil.rmtree(item_path)

    def clear_runtime_storage(self): 
        # clear application storage
        self._clear_dir(self._storage.storage_dir())

        # clear git file system
        self._clear_dir(self._gfs.storage_dir())

    def clear_logs(self): 
        # TODO: also disable logging for the rest of the execution
        # TODO: actions from the admin page (clear_logs(), clear_runtime_storage(), test_manatee()) 
        #       should be done with redirect just as any other action such as getwin (see controller.py)
        os.remove(LOG_FILE)
        os.remove(SUBPROCESS_LOG_FILE)

    def test_manatee(self): 
        import manatee

        # this corpus is on aurora.fi.muni.cz
        corpus = manatee.Corpus('/nlp/projekty/editor_korpusu/public_html/korpus_wiki_parallel_cs/wiki_parallel_cs')
        assert corpus.get_conf('VERTICAL') == '/nlp/projekty/editor_korpusu/public_html/korpus_wiki_parallel_cs/cs-vert.vert'

    def _file_path_for_corpus(self, corpus_name): 
        return vertical_path(corpus_name)
        #import manatee

        #corpus = manatee.Corpus(corpus_name)
        #return corpus.get_conf('VERTICAL')

    def window_page(self, window_id, catch_exc=True):
        if catch_exc: 
            try:
                window = self._load_window(window_id)
                pgdata = window.page_data()
            except Exception as e: 
                pgdata = self._error_page_data(e) 
        else: 
            window = self._load_window(window_id)
            pgdata = window.page_data()

        return self._complete_page_data(pgdata)

    def window_ajax(self, window_id, line=None, save_vpc=None):
        window = self._load_window(window_id)

        if save_vpc is not None: 
            # viewport content changed (the user made an edit)
            window.save_viewport_content(save_vpc)

        if line != None: 
            # move the viewport
            window.set_line(line)

        data = window.ajax_data(line)
        self._storage.save_window(window)

        return data

    def window_ajax_find_before(self, window_id, line, search_string, save_vpc=None): 
        window = self._load_window(window_id)

        if save_vpc is not None: 
            # viewport content changed (the user made an edit)
            window.save_viewport_content(save_vpc)

        window.set_line_find_before(line, search_string)
        data = window.ajax_data()
        self._storage.save_window(window)

        return data

    def window_ajax_find_after(self, window_id, line, search_string, save_vpc=None): 
        window = self._load_window(window_id)

        if save_vpc is not None: 
            # viewport content changed (the user made an edit)
            window.save_viewport_content(save_vpc)

        window.set_line_find_after(line, search_string)
        data = window.ajax_data()
        self._storage.save_window(window)

        return data


    def window_suggestions(self, window_id, wordtype, word): 
        try:
            if wordtype == 'morphattr': 
                attr_name = word

                window = self._load_window(window_id)

                corpus_name = window.corpus_name()
                import manatee
                c = manatee.Corpus(corpus_name)
                attr = c.get_attr(attr_name);
                num_items = attr.id_range()

                suggestions = []
                for i in range(0, num_items): 
                    suggestions.append(attr.id2str(i))

                self._storage.save_window(window)

                data = json.dumps({'suggestions': suggestions, 'error': 'none'})

            elif wordtype == 'structattr': 
                attr_name = word

                window = self._load_window(window_id)

                corpus_name = window.corpus_name()
                import manatee
                c = manatee.Corpus(corpus_name)
                attrs_string = c.get_conf('STRUCTATTRLIST');
                attrs = attrs_string.split(',')

                suggestions = []
                for a in attrs: 
                    suggestions.append(a.split('.')[1])

                self._storage.save_window(window)

                data = json.dumps({'suggestions': suggestions, 'error': 'none'})

        except Exception as e: 
            data = self._error_ajax_data(e)

        return data


    def save_viewport_content(self, window_id, new_content): 
        window = self._storage.load_window(window_id)
        window.save_viewport_content(new_content)
        self._storage.save_window(window)

    def commit(self, window_id): 
        window = self._storage.load_window(window_id)
        window.commit()
        self._storage.save_window(window)

    def lock(self, window_id): 
        # locks the file
        window = self._storage.load_window(window_id)
        window.lock()
        self._storage.save_window(window)

    def unlock(self, window_id): 
        # unlocks the file
        window = self._storage.load_window(window_id)
        window.unlock()
        self._storage.save_window(window)


def vertical_path(corpus_name): 
    import manatee

    corpus = manatee.Corpus(corpus_name)
    file_path = corpus.get_conf('VERTICAL')

    if os.path.isabs(file_path): 
        return file_path
    else:
        # The VERTICAL in the config file is a relative path 
        # (relative from the directory where the config file is). 
        # Get the absolute version of the VERTICAL path.
        # NOTE: (tested on the susanne corpus I compiled a long ago): 
        #       doesn't choose the correct base dir for the rel. path? 
        #       (I moved the "config" file from susanne one dir up and it 
        #       works that way; not sure if the problem is here or there)
        #       TODO: test it on some surely well compiled corpuses
        assert os.path.exists(corpus_name)
        orig_wd = os.getcwd()
        os.chdir(os.path.dirname(corpus_name))
        abs_file_path = os.path.abspath(file_path)
        os.chdir(orig_wd)
        return abs_file_path



#class ApplicationStorage(JSONStorage):  # NOTE: this worked but now we use PickleStorage instead
class ApplicationStorage(PickleStorage): 
    def __init__(self, directory):
        #super(ApplicationStorage, self).__init__(self, directory)
        PickleStorage.__init__(self, directory)


    def load_session(self, session_id): 
        return self.load(class_=Session, 
                args_to_key_func=Session.make_id, 
                args={'session_id': session_id}, 
                obj_to_key_func=Session.get_id)

    def save_session(self, s): 
        assert isinstance(s, Session)
        return self.save(obj_to_key_func=Session.get_id, obj=s)

    def create_session(self, s): 
        assert isinstance(s, Session)
        return self.create(obj_to_key_func=Session.get_id, obj=s)

    def delete_session(self, s): 
        assert isinstance(s, Session)
        return self.delete(obj_to_key_func=Session.get_id, obj=s)


    def load_window(self, window_id): 
        return self.load(class_=Window, 
                args_to_key_func=Window.make_id, 
                args={'window_id': window_id}, 
                obj_to_key_func=Window.get_id)

    def save_window(self, w): 
        assert isinstance(w, Window)
        return self.save(obj_to_key_func=Window.get_id, obj=w)

    def create_window(self, w): 
        assert isinstance(w, Window)
        return self.create(obj_to_key_func=Window.get_id, obj=w)

    def delete_window(self, w): 
        assert isinstance(w, Window)
        return self.delete(obj_to_key_func=Window.get_id, obj=w)


class Session: 
    VIEWPORT_STYLE_PLAIN_TEXTAREA = 'plain_textarea'
    VIEWPORT_STYLE_RICH_TEXTAREA = 'rich_textarea'
    CONFIG_DEFAULT_VP_NLINES = 10

    def __init__(self, session_id=None): 
        if session_id is None: 
            session_id = idgen.new_id()
        self._session_id = session_id

        self.set_viewport_style(Session.VIEWPORT_STYLE_RICH_TEXTAREA) 
        self.set_default_viewport_nlines(Session.CONFIG_DEFAULT_VP_NLINES)
        self._window_ids = dict()  # keep track of windows (observer pattern)

    def get_id(self): 
        return self._session_id

    @classmethod
    def make_id(cls, session_id): 
        return session_id


    def window_ids(self): 
        return self._window_ids

    def set_viewport_style(self, style): 
        self._viewport_style = style

    def viewport_style(self): 
        return self._viewport_style

    def set_default_viewport_nlines(self, nlines): 
        self._default_vp_nlines = nlines

    def default_viewport_nlines(self): 
        return self._default_vp_nlines


    def register_window(self, window_id): 
        self._window_ids[window_id] = True

    def unregister_window(self, window_id): 
        del self._window_ids[window_id]

    #def window(self, window_id): 
    #    return Application().window(window_id)
        


# TODO: Tests specifically for the Window class (not just indirectly through Application).
# TODO: Fix this annoying behavior of Application.window_page(): if get_viewport_content() raises 
#       an exception, it doesn't bubble all the way up and instead we get KeyError; 
#       because of this, I then have to debug the issue by calling get_viewport_content() directly 
#       to see why it failed.
# TODO: Clean up old stuff that is no longer used.
class Window: 
    def __init__(self, window_id, session_id, file_path, corpus_name, revision, 
            viewport_line=None, viewport_nlines=10, 
            file_changelog=u'', basic_mode=False): 
        '''re-construct an existing window'''
        # NOTE: the file_changelog argument here means the changelog of this window
        #       (returned as window_changelog by page_data() and ajax_data())

        self._window_id = window_id
        self._session_id = session_id
        self._file_path = file_path
        self._corpus_name = corpus_name
        self._revision = revision  # the base revision of this window
                                   # NOTE: a window's base revision stays the same throughout its lifetime, 
                                   #       even after it's no longer the head revision
        self._viewport_line = viewport_line
        self._viewport_nlines = viewport_nlines
        self._window_changelog = file_changelog  # changelog from the base revision to the current state
                                                 # that is, all the changes made in this window's lifetime 
        self._basic_mode = basic_mode

        if self._basic_mode: 
            assert os.path.isfile(file_path)
        else:
            assert GitFileSystem().has_file(file_path)



    @classmethod
    def new(cls, session_id, file_path, corpus_name, revision=None, 
            viewport_line=None, viewport_nlines=10, 
            basic_mode=False, pos=None): 
        '''create a new window'''

        window_id = idgen.new_id()

        if basic_mode: 
            # basic mode means that in this window, the file is to be accessed read-only 
            # in its original location (without possibility of modification, without a VCS repository)
            pass
        else: 
            # if the file isn't being edited yet, create its VCS repository
            if not GitFileSystem().has_file(file_path): 
                #t1 = time()
                GitFileSystem().add_file(file_path)
                #t2 = time()
                #print "GitFileSystem.add_file took %f seconds" % (t2 - t1)

            if corpus_name != None: 
                GitFileSystem().assign_corpus_name(file_path, corpus_name)

            # NOTE: revision can be left as None only if the current corpus has been compiled 
            #       from the head revision. Otherwise revision must be set to the revision 
            #       the current corpus has been compiled from.  This is needed for proper 
            #       functioning of manatee.
            if revision is None:
                revision = GitFileSystem().head_revision(file_path)


        # if a position is given, find the line for the position
        assert pos != None or viewport_line != None
        assert not (pos != None and viewport_line != None)
        if pos != None: 
            # NOTE: We can only find the line number for position in the physical file.
            #       We will then use that line number for loading the segment, that is, 
            #       addressing the virtual file. For that to be correct, the physical 
            #       and the virtual file must be the same. That means the file changelog 
            #       must be empty. Because of this, we can only jump to a line when creating 
            #       a new window, NOT in a window that already has some edits in it.
            #       This is OK for integration with SketchEngine.

            if basic_mode:
                # there is no index in the basic mode
                with io.open(file_path, 'r', encoding='utf-8') as file_io:
                    line_read_io = segmentio.FileLineReadIO(file_io)
                    viewport_line = line_read_io.line_containing_pos(pos)
            else:
                # use the index that is in the repository 
                with io.open(file_path, 'r', encoding='utf-8') as file_io:
                    index = segmentio.LineIndex(GitFileSystem().file_fspath(file_path) + '.index')
                    line_read_io = segmentio.FileLineReadIO(file_io, index)
                    viewport_line = line_read_io.line_containing_pos(pos)


        if basic_mode: 
            window = cls(
                    window_id=window_id, 
                    session_id=session_id, 
                    file_path=file_path, 
                    corpus_name=corpus_name, 
                    revision=None, 
                    viewport_line=viewport_line, 
                    viewport_nlines=viewport_nlines, 
                    basic_mode=True)
        else: 
            window = cls(
                    window_id=window_id, 
                    session_id=session_id, 
                    file_path=file_path, 
                    corpus_name=corpus_name, 
                    revision=revision, 
                    viewport_line=viewport_line, 
                    viewport_nlines=viewport_nlines)


        return window


    def get_id(self): 
        return self._window_id

    @classmethod
    def make_id(cls, window_id): 
        return window_id


    def file_path(self): 
        return self._file_path
    def corpus_name(self): 
        return self._corpus_name
    def viewport_line(self): 
        return self._viewport_line
    def viewport_nlines(self): 
        return self._viewport_nlines


    def page_data(self): 
        vpc = self.get_viewport_content()  # NOTE: only for testing; the real editor gets the content from ajax_data()
        if self._basic_mode: 
            changelog_from_head = "(no changelog_from_head, \nas this window is in basic mode)"
            total_changelog = "(no total_changelog, \nas this window is in basic mode)"
        else: 
            changelog_from_head = self.changelog_from_head() 
            total_changelog = self.total_changelog()
        return {'page_type': 'window', 
                'title': 'corpedit window', 
                'window_id': self.get_id(), 
                'basic_mode': self._basic_mode, 
                'viewport_content': vpc, 
                'viewport_line': self._viewport_line, 
                'viewport_nlines': self._viewport_nlines, 
                'file_path': self._file_path, 
                'corpus_name': self._corpus_name, 
                'revision': self._revision, 
                'changelog_from_head': changelog_from_head, 
                'window_changelog': self._window_changelog, 
                'total_changelog': total_changelog, 
                'orig_window_status': 'this window from page load: ' + unicode(self.__dict__)}

    def set_line(self, line): 
        self._viewport_line = line

    def set_line_find_before(self, line, search_string): 
        my_io = self._my_io()
        found_line = my_io.find_before(line, search_string)
        self.set_line(found_line)

    def set_line_find_after(self, line, search_string): 
        my_io = self._my_io()
        found_line = my_io.find_after(line, search_string)
        self.set_line(found_line)

    def ajax_data(self, line=None): 
        #if line is not None: 
        #    # line changed (the user scrolled)
        #    self._viewport_line = line

        vpc = self.get_viewport_content()
        dbg(vpc)

        if GitFileSystem().file_is_cmtlocked(self._file_path): 
            file_lock = 'locked'
        else: 
            file_lock = 'not_locked'

        if self._basic_mode: 
            changelog_from_head = "(no changelog_from_head, \nas this window is in basic mode)"
            total_changelog = "(no total_changelog, \nas this window is in basic mode)"
        else: 
            changelog_from_head = self.changelog_from_head() 
            total_changelog = self.total_changelog()
        data = json.dumps({
            'viewport_line': self._viewport_line, 
            'viewport_content': vpc, 
            'changelog_from_head': changelog_from_head, 
            'window_changelog': self._window_changelog, 
            'total_changelog': total_changelog, 
            'file_lock': file_lock, 
            'status': 'this window after ajax: ' + unicode(self.__dict__)})
        return data
    

    def total_changelog(self): 
        '''changelog from head to current state represented by this window (including saved changes)'''

        if self._basic_mode: 
            return self._window_changelog
        else: 
            physical_file = GitFileSystem().file_fspath(self._file_path)

            diff_from_head = GitFileSystem().diff_from_head(self._file_path, self._revision)
            changelog_from_head = segmentio.changelog_from_patch_file_content(diff_from_head)

            if changelog_from_head == u'': 
                window_changelog_on_head = self._window_changelog
            else:
                changelog_to_head = self.changelog_to_head()
                window_changelog_on_head = segmentio.rebase_changelog(
                        self._window_changelog, changelog_to_head)

            changelog = window_changelog_on_head

            dbg("changelog_from_head:", changelog_from_head)
            dbg("self._window_changelog:", self._window_changelog)
            dbg("total_changelog:", changelog)

            return changelog


    def changelog_from_head(self): 
        #assert not self._basic_mode
        '''changelog from head to the base revision (self._revision) of this window (without saved changes)'''
        if self._basic_mode: 
            return u''
        else: 
            diff_from_head = GitFileSystem().diff_from_head(self._file_path, self._revision)
            changelog_from_head = segmentio.changelog_from_patch_file_content(diff_from_head)
            return changelog_from_head

    def changelog_to_head(self): 
        return segmentio.invert_changelog(self.changelog_from_head())


    def rebase_to_head(self): 
        '''rebase the window from its current revision to the head revision'''
        self._window_changelog = segmentio.rebase_changelog(self._window_changelog, self.changelog_to_head())
        self._revision = GitFileSystem().head_revision(self._file_path)


    def _my_io(self): 
        if self._basic_mode: 
            physical_file = self._file_path
            file_io = io.open(physical_file, 'r', encoding='utf-8')
            line_read_io = segmentio.FileLineReadIO(file_io)
            my_io = segmentio.SegmentIO(line_read_io, self._window_changelog)
        else: 
            if self._revision != GitFileSystem().head_revision(self._file_path): 
                self.rebase_to_head()
            assert self._revision == GitFileSystem().head_revision(self._file_path)

            physical_file = GitFileSystem().file_fspath(self._file_path)

            #diff_from_head = GitFileSystem().diff_from_head(self._file_path, self._revision)
            #changelog_from_head_to_my_base = segmentio.changelog_from_patch_file_content(diff_from_head)

            file_io = io.open(physical_file, 'r', encoding='utf-8')
            index = segmentio.LineIndex(physical_file + '.index')
            headrev_io = segmentio.FileLineReadIO(file_io, index)
            #my_base_io = segmentio.SegmentIO(headrev_io, changelog_from_head_to_my_base)
            #my_io = segmentio.SegmentIO(my_base_io, self._window_changelog)
            ###total_changelog = self.total_changelog()
            ###my_io = segmentio.SegmentIO(headrev_io, total_changelog)
            my_io = segmentio.SegmentIO(headrev_io, self._window_changelog)

            #dbg(changelog_from_head_to_my_base)
            #dbg(self._window_changelog)

        return my_io




    def get_viewport_content(self):  # (see termdemo-get.sh)
        if not self._basic_mode:
            GitFileSystem().lock_file(self._file_path)

        my_io = self._my_io()
        seg = my_io.get_segment(block_begin_line=self._viewport_line, block_num_lines=self._viewport_nlines)
        content = seg.block_data()

        #file_io.close()

        #my_io.close()
        #my_base_io.close()
        #headrev_io.close()
        if not self._basic_mode:
            GitFileSystem().release_file(self._file_path)

        return content


    def save_viewport_content(self, new_content):  # (see termdemo-save.sh)
        if not self._basic_mode:
            GitFileSystem().lock_file(self._file_path)
        #if self._basic_mode:
        #    physical_file = self._file_path
        #    file_io = io.open(physical_file, 'r', encoding='utf-8')
        #    line_read_io = segmentio.FileLineReadIO(file_io)
        #    my_io = segmentio.SegmentIO(line_read_io, self._window_changelog)
        #else: 
        #    if self._revision != GitFileSystem().head_revision(self._file_path): 
        #        self.rebase_to_head()
        #    assert self._revision == GitFileSystem().head_revision(self._file_path)

        #    physical_file = GitFileSystem().file_fspath(self._file_path)

        #    #changelog = self.total_changelog()
        #    #fio = io.open(physical_file, 'r', encoding='utf-8')
        #    #sio = segmentio.SegmentIO(fio, changelog)
        #    #seg = sio.get_segment(block_begin_line=self._viewport_line, block_num_lines=self._viewport_nlines)

        #    # NOTE: The above approach was incorrect. It bases the SegmentIO on the head revision and that 
        #    #       causes the "self._window_changelog = sio.file_changelog()" command below to store the 
        #    #       changelog **from the head revision** in self._window_changelog. That is incorrect, as 
        #    #       self._window_changelog should be the changelog **from the base revision of this window**.
        #    #
        #    #       The correct approach is to base the SegmentIO on the base revision of this window.
        #    #       That means it itself needs to be based on a SegmentIO with the changelog from the 
        #    #       head revision to the base revision of this window. 
        #    # 
        #    #       I made basing a SegmentIO on another SegmentIO possible by making this change 
        #    #       in segmentio.py: 
        #    #
        #    #           * SegmentIO no longer takes an ordinary IO to access the physical file. 
        #    #           Instead, it takes a LineReadIO instance. LineReadIO is an interface. 
        #    #           To implement it, one needs to provide a function that reads lines.
        #    #
        #    #           * SegmentIO implements LineReadIO, providing a function to read lines 
        #    #           of a virtual file. This makes it possible to base a SegmentIO on 
        #    #           another SegmentIO.
        #    #
        #    #           * FileLineReadIO implements LineReadIO, providing a function to read lines 
        #    #           of a physical file. It can be given an index to find the lines efficiently. 
        #    #           NOTE: The index for each file is generated only once, for the initial revision 
        #    #                 when the file is added to the GitFileSystem.
        #    #                 To avoid having to re-generate the index after every commit, a VirtualIndex 
        #    #                 is used as the index for the head revision. It takes the index for the 
        #    #                 initial revision and shifts it using the OffsetTable of the changelog 
        #    #                 from the initial revision to the head revision.

        #    #diff_from_head = GitFileSystem().diff_from_head(self._file_path, self._revision)
        #    #changelog_from_head_to_my_base = segmentio.changelog_from_patch_file_content(diff_from_head)

        #    file_io = io.open(physical_file, 'r', encoding='utf-8')
        #    index = segmentio.LineIndex(physical_file + '.index')
        #    headrev_io = segmentio.FileLineReadIO(file_io, index)
        #    #my_base_io = segmentio.SegmentIO(headrev_io, changelog_from_head_to_my_base)
        #    #my_io = segmentio.SegmentIO(my_base_io, self._window_changelog)
        #    ###total_changelog = self.total_changelog()
        #    ###my_io = segmentio.SegmentIO(headrev_io, total_changelog)
        #    my_io = segmentio.SegmentIO(headrev_io, self._window_changelog)

        my_io = self._my_io()
        seg = my_io.get_segment(block_begin_line=self._viewport_line, block_num_lines=self._viewport_nlines)

        #dbg(seg._old_segment_data)
        #dbg(seg._segment_data)
        #dbg(seg.changelog(lineNumbersFromDest=True))

        #dbg(self._window_changelog)
        #dbg("before:", my_io.file_changelog())

        seg.set_block_data(new_content)
        # TODO before saving the segment, check for collision with any other window of any user
        #      idea: first back up the things that are changed by save_viewport_content(); then save and check 
        #            if file_changelog has any intersecting lines with any other window's file_changelog; 
        #            if it does, restore the previous state from backup and raise an exception
        my_io.save_segment(seg)
        self._window_changelog = my_io.file_changelog()  

        #dbg("after:", my_io.file_changelog())

        #file_io.close()
        #my_io.close()
        #my_base_io.close()
        #headrev_io.close()
        if not self._basic_mode:
            GitFileSystem().release_file(self._file_path)


    def commit(self): 
        assert not self._basic_mode

        GitFileSystem().lock_file(self._file_path)

        #diff_from_head = GitFileSystem().diff_from_head(self._file_path, self._revision)
        #changelog_from_head = segmentio.changelog_from_patch_file_content(diff_from_head)
        #changelog = segmentio.compose_changelogs(changelog_from_head, self._window_changelog)
        ###changelog = self.total_changelog()
        assert self._revision == GitFileSystem().head_revision(self._file_path)
        changelog = self._window_changelog

        patchfile = u'--- \n+++ \n' + changelog
        GitFileSystem().patch_and_commit_file(self._file_path, patchfile)

        self._window_changelog = u''

        GitFileSystem().release_file(self._file_path)


    def lock(self): 
        assert not self._basic_mode
        success = GitFileSystem().cmtlock_file(self._file_path)
        assert success

    def unlock(self): 
        assert not self._basic_mode
        success = GitFileSystem().cmtunlock_file(self._file_path)
        assert success



class GitFileSystem(Singleton):  # (see termdemo.sh)
    def __init__(self, main_dir=None, username=None): 

        # TODO: fix this in singleton.py
        #       (hand-testing revealed it doesn't actually raise the exception when there are no instances)
        #       otherwise the singleton works: 
        #            >>> from model import GitFileSystem
        #            >>> gfs = GitFileSystem(main_dir='kak')
        #            >>> gfs._main_dir
        #            'kak'
        #            >>> g = GitFileSystem()
        #            >>> gfs._main_dir
        #            'kak'
        #            >>> g._main_dir
        #            'kak'
        if main_dir is None: 
            # constructor called without args (just getting an instance; see Singleton)
            if self.__class__._instances is None: 
                # getting an instance but the singleton doesn't exist yet -> error: 
                raise Exception('error: cannot get an instance of Application the instance does not exist yet')
            else: 
                # getting an instance, the singleton instance exists already -> OK, 
                # __init__() doesn't do anything in this case
                return 

        self._main_dir = main_dir

        if username == None: 
            self._username = 'GFS_USER'
        else: 
            self._username = username


    def storage_dir(self): 
        return self._main_dir


    def has_file(self, file_path): 
        repo_dir = self._repo_dir(file_path)
        if os.path.isdir(repo_dir): 
            return True
        else: 
            return False


    def all_files(self): 
        files = []
        items = os.listdir(self._main_dir)
        for item in items: 
            repo_dir = os.path.join(self._main_dir, item)

            if os.path.isdir(repo_dir): 
                with io.open(os.path.join(repo_dir, 'origpath')) as f: 
                    file_path = f.readline().rstrip()

                if os.path.isfile(os.path.join(repo_dir, 'corpus')): 
                    with io.open(os.path.join(repo_dir, 'corpus')) as f: 
                        corpus_name = f.readline().rstrip()
                else: 
                    # no corpus name assigned yet
                    corpus_name = None

                files.append({'file_path': file_path, 'corpus_name': corpus_name})

        return files


    def assign_corpus_name(self, file_path, corpus_name): 
        '''Assigns the corpus name to the file to let it be known that 
        the file can be accessed through that corpus name.
        Call this method when someone accesses the file by corpus name. 
        '''
        assert self.has_file(file_path)
        with io.open(os.path.join(self._repo_dir(file_path), 'corpus'), 'w') as f: 
            f.write(unicode(corpus_name + os.linesep))


    def add_file(self, file_path): 
        #assert os.stat(file_path).st_nlink == 1
        # NOTE: These link count checks are made on the premise that each file is only repoed once. 
        #       When there are multiple users editing the same file, each user has the file in their 
        #       repo so the link count is more than 2. 
        #
        #       Even running all the tests in model_test.ApplicationTestCase means there are multiple 
        #       users per file.
        #
        #       So uncomment these checks only when you need to debug with just one user (such as 
        #       when debugging a single test).

        assert not self.has_file(file_path)

        # make the repo directory for the file
        repo_dir = self._repo_dir(file_path)
        os.mkdir(repo_dir)

        # link the file into the repo directory
        repoed_file_path = self.file_fspath(file_path)
        self._create_link(file_path, repoed_file_path)

        # put a .gitignore file in the repo directory to prevent git from 
        # tracking the index file, the origpath file, and the corpus name file
        with io.open(os.path.join(repo_dir, '.gitignore'), 'w', encoding='utf-8') as f: 
            index_file_name = os.path.basename(file_path) + '.index'
            f.write(unicode(index_file_name + os.linesep))
            f.write(unicode('origpath' + os.linesep))
            f.write(unicode('corpus' + os.linesep))

        # set up (init; add -A; commit) a git repository in the repo directory
        self._set_up_git_repo(repo_dir)

        # build the index
        segmentio.LineIndex.build(repoed_file_path, repoed_file_path + '.index')

        # create the origpath file: that is a file containing file_path 
        # (it is not really necessary to have such file but good for clarity; 
        # it allows to identify which file this repository belongs to and 
        # restore the link any time later if it is broken for some reason)
        with io.open(os.path.join(repo_dir, 'origpath'), 'w', encoding='utf-8') as f: 
            f.write(unicode(file_path + os.linesep))

        assert self.has_file(file_path)

        #dbg(["LINKCOUNT_ORIG", os.stat(file_path).st_nlink])
        #dbg(["LINKCOUNT_REPOED", os.stat(repoed_file_path).st_nlink])
        #assert os.stat(file_path).st_nlink == 2
        #assert os.stat(repoed_file_path).st_nlink == 2


    def file_fspath(self, file_path): 
        '''returns the path of the file in the system (that is, in its git repository)'''
        repo_dir = self._repo_dir(file_path)
        file_basename = os.path.basename(file_path)
        return os.path.join(repo_dir, file_basename)


    def remove_file(self, file_path): 
        assert self.has_file(file_path)

        repo_dir = self._repo_dir(file_path)
        shutil.rmtree(repo_dir)

        assert not self.has_file(file_path)


    def cmtlock_file(self, file_path): 
        '''locks file against commits'''
        file_id = self._file_id(file_path)
        lockdir = os.path.join(self._main_dir, file_id + '_cmtlock')

        # TODO use lockdir.py
        try: 
            os.mkdir(lockdir)
            # locked successfully
            return True

        except OSError: 
            # couldn't lock
            return False


    def cmtunlock_file(self, file_path): 
        '''unlocks file so it can be committed to again'''
        file_id = self._file_id(file_path)
        lockdir = os.path.join(self._main_dir, file_id + '_cmtlock')

        try: 
            os.rmdir(lockdir)
            # unlocked successfully
            return True

        except OSError: 
            # couldn't unlock
            return False


    def file_is_cmtlocked(self, file_path): 
        '''checks if the file is locked against commits'''
        file_id = self._file_id(file_path)
        lockdir = os.path.join(self._main_dir, file_id + '_cmtlock')

        return os.path.isdir(lockdir)


    def lock_file(self, file_path):
        repo_dir = self._repo_dir(file_path)
        lockdir.lock(repo_dir, lockdir.RWLOCK)
        assert lockdir.is_locked(repo_dir, lockdir.RWLOCK)
        assert lockdir.pid_of_lock(repo_dir, lockdir.RWLOCK) == os.getpid()

    def release_file(self, file_path): 
        repo_dir = self._repo_dir(file_path)
        lockdir.release(repo_dir, lockdir.RWLOCK)


    def head_revision(self, file_path):
        assert self.has_file(file_path)
        repo_dir = self._repo_dir(file_path)
        repoed_file_path = self.file_fspath(file_path)

        # NOTE: This function is always called before reading or writing the file.
        #       As such a bottleneck, it executes the steps (1) and (2) to get the 
        #       file in the user's personal repository in sync with the state of the 
        #       physical file, before the repoed file in it is read from or written to
        #       in any way. 
        #       
        # TODO: The whole process of accessing the file, including these steps, 
        #       should be an atomic transaction. Optionally (would be nice), distinguish 
        #       read-only access (can be non-exclusive) and read/write access (must be exclusive). 

        # (1)
        # the physical file and the repoed file must be hardlinked, 
        # that is: be two hardlinks to the same file
        # (if they are not, _fix_broken_link will take the physical file and 
        # recreate the repoed file as a hardlink to it)
        self._fix_broken_link(file_path, repoed_file_path, push=False)
        assert self._is_link(file_path, repoed_file_path)

        # (2)
        # the HEAD revision must be the physical file
        # (if it is not, _catch_up() will make it so)
        self._catch_up(repo_dir)
        #assert not self._unstaged_changes(repo_dir)
        assert self._is_link(file_path, repoed_file_path)

        orig_wd = os.getcwd()
        os.chdir(repo_dir)
        output = subprocess.check_output(["git", "rev-list", "HEAD"])
        os.chdir(orig_wd)

        return output.splitlines()[0]  # the first revision in the rev-list is the head revision


    def diff_from_head(self, file_path, revision):
        assert self.has_file(file_path)
        repo_dir = self._repo_dir(file_path)
        headrev = self.head_revision(file_path)

        orig_wd = os.getcwd()
        os.chdir(repo_dir)
        output = subprocess.check_output(["git", "diff", "--unified=0", headrev, revision])
        os.chdir(orig_wd)

        #print output
        return output.decode('utf-8')


    def patch_and_commit_file(self, file_path, patchfile_from_head):
        # NOTE: rewrites the file, may take a long time (unlike any other operation)

        assert self.has_file(file_path)
        repo_dir = self._repo_dir(file_path)
        repoed_file_path = self.file_fspath(file_path)
        assert self._is_link(file_path, repoed_file_path)

        assert not self.file_is_cmtlocked(file_path)  # the file must not be locked against commits

        orig_wd = os.getcwd()
        os.chdir(self._repo_dir(file_path))

        #assert os.stat(file_path).st_nlink == 2
        #assert os.stat(repoed_file_path).st_nlink == 2

        # patch the file
        tmp_patchfile = os.path.join(repo_dir, 'tmp.patch')
        with io.open(tmp_patchfile, 'w', encoding='utf-8') as f: 
            f.write(patchfile_from_head)
        #orig_inode_number = os.stat(repoed_file_path).st_ino
        returncode = subprocess_call(["patch", repoed_file_path, tmp_patchfile])
        # NOTE: When the patch utility overwrites the file, it breaks the hardlink.
        #       Because of that, I move the (now broken off) repoed file into the original file 
        #       and hardlink it into the repository again. This way of doing it also makes 
        #       commit an atomic operation (because mv is atomic).
        #
        #       When the changelog is empty, the patch utility doesn't overwrite the file 
        #       and both the hardlinks (the original file and the repoed file) stay as the were. 
        #       Thus nothing needs to be done.
        #
        #inode_number_after_patch = os.stat(repoed_file_path).st_ino
        #assert ((os.stat(file_path).st_nlink == 2 \
        #        and os.stat(repoed_file_path).st_nlink == 2 \
        #        and inode_number_after_patch == orig_inode_number) 
        #        or (os.stat(file_path).st_nlink == 1 \
        #                and os.stat(repoed_file_path).st_nlink == 1 \
        #                and inode_number_after_patch != orig_inode_number))
        self._fix_broken_link(file_path, repoed_file_path, push=True)

        #print "~~~"
        #print subprocess.check_output(["patch", self.file_fspath(file_path), tmp_patchfile])
        #print "~~~"
        #with io.open(self.file_fspath(file_path), 'r', encoding='utf-8') as f: 
        #    print f.read()
        dbg(patchfile_from_head)

        assert returncode == 0
        os.remove(tmp_patchfile)

        # add and commit
        returncode = subprocess_call(["git", "add", "-A"])
        assert returncode == 0

        returncode = subprocess_call(["git", "commit", "-m", 
            "GitFileSystem(user: %s): user commit" % self._username])
        assert returncode == 0
        assert self._is_link(file_path, repoed_file_path)

        # rebuild the index
        segmentio.LineIndex.build(repoed_file_path, repoed_file_path + '.index')

        os.chdir(orig_wd)

        # NOTE: After the file is rewritten, any new windows (Window.new()) must be created 
        #       with the 'revision' argument set to the revision the current corpus has been compiled from.
        #       Otherwise manatee wouldn't work.


    def _file_id(self, file_path): 
        return md5(file_path).hexdigest()  # NOTE: relying on that the hashes don't collide

    def _repo_dir(self, file_path): 
        dbg(os.getcwd())
        dbg(self._main_dir)
        assert os.path.isdir(self._main_dir)
        file_id = self._file_id(file_path)
        repo_dir = os.path.join(self._main_dir, file_id)
        return repo_dir

    def _create_link(self, source, link_name): 
        #os.symlink(file_path, repoed_file_path)  # symlink() instead of link() bacause
        #                                         # hardlinks can't be made from one disk to another 
        #                                         #
        #                                         # symlinking requires file_path to be absolute
        #
        # NOTE: Hardlinking, not symlinking. The approach above in this comment (symlinking) didn't work 
        #       because git can't follow symlinks. 
        #       So we use hardlinks. Because of this, main_dir must be on the same disk as the edited files. 
        os.link(source, link_name)
        assert self._is_link(source, link_name)

    def _is_link(self, source, link_name): 
        '''Checks if the file <link_name> is hardlinked with the file <source>.
        '''
        if os.stat(link_name).st_nlink == 1: 
            # hardlink count only 1 (that is: not a link to anywhere else other than itself) 
            return False

        link_name_inode_number = os.stat(link_name).st_ino
        source_inode_number = os.stat(source).st_ino
        if link_name_inode_number != source_inode_number: 
            # source and link_name are NOT hardlinked (they have different inode numbers)
            # (that is: the link is broken)
            return False

        #with io.open(link_name, 'r') as f: 
        #    if not f.readable(): 
        #        return False

        return True

    def _fix_broken_link(self, source, link_name, push=False): 
        '''Call this function whenever the hardlink could have been broken 
        (such as after calling patch). If the link is broken, it fixes it.

        push==True:
            The broken link will be resolved by `mv link_name source' and then re-creating the link. 
            This replaces the <source> file.
            After a user commit, _fix_broken_link with this option must be called.
        push==False: 
            The broken link will be resolved by just recreating the link. 
            This keeps the <source> file intact.
            If calling _fix_broken_link in any other case than after a user commit, 
            this option must be used.

        Programs that write to the file, such as patch or git, can break the
        hardlink. After calling such an external program to write to the file, 
        call this function on that file to fix the link in case the program broke it.
        '''
        dbg('FIXBL')

        if not self._is_link(source, link_name): 
            if push:
                returncode = subprocess_call(["mv", link_name, source])
                assert returncode == 0
                # NOTE: mv replaced <source>'s inode number with the inode number of <link_name>. 
                #       That broke every other user's hardlink to <source>. 
                #       Everyone must take care of this by calling _fix_broken_link with push=False 
                #       before using the file in their repository.
                #
                #       head_revision() is the single function that takes care of this, 
                #       just like it takes care of calling _catch_up().

            self._create_link(source, link_name)

        assert self._is_link(source, link_name)

    def _set_up_git_repo(self, repo_dir): 
        orig_wd = os.getcwd()
        os.chdir(repo_dir)

        returncode = subprocess_call(["git", "init"])
        assert returncode == 0

        returncode = subprocess_call(["git", "config", "user.name", self._username])
        assert returncode == 0
        returncode = subprocess_call(["git", "config", "user.email", "nothing@example.com"])
        assert returncode == 0

        returncode = subprocess_call(["git", "add", "-A"])
        assert returncode == 0

        returncode = subprocess_call(["git", "commit", "-m", 
            "GitFileSystem(user: %s): initial commit" % self._username])
        assert returncode == 0

        os.chdir(orig_wd)


    def _unstaged_changes(self, repo_dir): 
        '''checks if there are unstaged changes'''
        orig_wd = os.getcwd()
        os.chdir(repo_dir)
        dbg('STATUS in repo %s: \n' % repo_dir, subprocess.check_output(["git", "status"]))
        returncode = subprocess_call(["git", "diff", "--exit-code"])
        # NOTE: This bug is relevant when using DBG_WHITELIST in common.py to filter the log.
        # FIXME: this is possibly some weird bug in common.py???
        # <--- When I put dbg('STATUS') here, the stack trace in the log 
        #      doesn't show the contents of the lines.
        #
        #      It looks like this: 
        #
        #      DEBUG:root:
        #        File "model_test.py", line 282, in test_do_some_edits_parallel_workflow
        #        File "model.py", line 86, in open_window
        #        File "model.py", line 338, in new
        #        File "model.py", line 625, in head_revision
        #        File "model.py", line 810, in _catch_up
        #        File "model.py", line 775, in _unstaged_changes
        #        File "../common.py", line 83, in dbg
        #      #[STATUS]#
        #
        #dbg('STATUS')
        os.chdir(orig_wd)
        # <--- When I put dbg('STATUS') here, the stack trace is normal.
        #
        #      It looks like this: 
        #
        #      DEBUG:root:
        #        File "model_test.py", line 282, in test_do_some_edits_parallel_workflow
        #          w1_id = model.Application().open_window(file_path, None, 67, 5)
        #        File "model.py", line 86, in open_window
        #          viewport_nlines=(self._session.default_viewport_nlines() if nlines is None else nlines))
        #        File "model.py", line 338, in new
        #          revision = GitFileSystem().head_revision(file_path)
        #        File "model.py", line 625, in head_revision
        #          self._catch_up(repo_dir)
        #        File "model.py", line 795, in _catch_up
        #          if self._unstaged_changes(repo_dir):
        #        File "model.py", line 779, in _unstaged_changes
        #          dbg('STATUS')
        #      #[STATUS]#
        #
        #dbg('STATUS')

        if returncode == 0: 
            dbg('UNSTAGED NO')
            return False
        else: 
            dbg('UNSTAGED YES')
            return True


    def _catch_up(self, repo_dir): 
        '''Makes the HEAD revision point to the physical file. If there are no unstaged changes 
        it does nothing. If there are unstaged changes it makes a commit to "catch up" with them. 

        When a user commits, it causes other users of that file to have unstaged changes.
        '''
        dbg('CATCHUP')

        if self._unstaged_changes(repo_dir): 
            orig_wd = os.getcwd()
            os.chdir(repo_dir)

            returncode = subprocess_call(["git", "add", "-A"])
            assert returncode == 0

            returncode = subprocess_call(["git", "commit", "-m", "GitFileSystem(user: %s): catch-up commit" % username])
            assert returncode == 0

            os.chdir(orig_wd)

        assert not self._unstaged_changes(repo_dir)
