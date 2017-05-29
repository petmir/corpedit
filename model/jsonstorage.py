#!/usr/bin/env python
# -*- coding: utf8 -*-

from jsondictio import JSONDictIO
import io, os


class DontHaveLockError(Exception): 
    def __init__(self): 
        Exception.__init__(self, 'error: you don\'t have lock (thread_safe is enabled so you need to get_lock())')


class JSONStorage: #TODO locking (transactions)
    PERMISSIONS = 0o777

    def __init__(self, directory, thread_safe=False):
        self._storage_dir = directory

        self._thread_safe = thread_safe
        self._i_have_lock = False
    
    # NOTE: for thread safety:
    #       1. call get_lock() before calling anything else in this class
    #       2. do whatever calls you need
    #       3. when done, call release_lock()
    def get_lock(self): 
        pass
        self._lockfile = open(self._storage_dir + '/' + 'storage.lock')
        fcntl.flock(self._lockfile, fcntl.LOCK_EX)  # blocking
        self._i_have_lock = True

    def release_lock(self): 
        pass
        self._lockfile.close()
        self._i_have_lock = False


    def _filename(self, classkey, objkey): 
        return self._storage_dir + '/' + classkey + '/' + objkey + '.json'

    def _class_dir_name(self, classkey): 
        return self._storage_dir + '/' + classkey

    def _ensure_class_dir(self, classkey): 
        class_dir = self._class_dir_name(classkey)
        if not os.path.isdir(class_dir): 
            os.mkdir(class_dir)
            if self.PERMISSIONS is not None: 
                os.chmod(class_dir, self.PERMISSIONS)
        assert os.path.isdir(class_dir)


    def _session_pk(session_id): 
        return session_id

    def _session_pk_for_session(s): 
        return s.session_id()



    def load(self, class_, args_to_key_func, args, obj_to_key_func): 
        if self._thread_safe and not self._i_have_lock: 
            raise DontHaveLockError()

        classkey = class_.__name__
        key = args_to_key_func(**args)
        filename = self._filename(classkey, key)

        try:
            text_io = io.open(filename, mode='r', encoding='utf-8')
        except IOError: 
            raise KeyError('cannot load: \n\
                    object %s %s \n\
                    does not exist in the storage \n\
                    (failed to open file "%s" for reading)' % (classkey, key, filename))
        dict_io = JSONDictIO(text_io)
        obj = class_.from_dict(dict_io.get())
        text_io.close()

        assert key == obj_to_key_func(obj)
        return obj


    def save(self, obj_to_key_func, obj): 
        if self._thread_safe and not self._i_have_lock: 
            raise DontHaveLockError()

        classkey = obj.__class__.__name__
        key = obj_to_key_func(obj)
        filename = self._filename(classkey, key)

        try:
            text_io = io.open(filename, mode='r+', encoding='utf-8')
        except IOError: 
            raise KeyError('cannot save: \n\
                    object %s %s \n\
                    does not exist in the storage \n\
                    (failed to open file "%s" for modification)' % (classkey, key, filename))
        dict_io = JSONDictIO(text_io)
        dict_io.set(obj.to_dict())
        text_io.close()


    def create(self, obj_to_key_func, obj): 
        if self._thread_safe and not self._i_have_lock: 
            raise DontHaveLockError()

        classkey = obj.__class__.__name__
        key = obj_to_key_func(obj)
        filename = self._filename(classkey, key)

        if os.path.isfile(filename): 
            raise KeyError('cannot create: \n\
                    object %s %s \n\
                    already exists in the storage \n\
                    (file %s exists)' % (classkey, key, filename))

        self._ensure_class_dir(classkey)
        text_io = io.open(filename, mode='w', encoding='utf-8')
        dict_io = JSONDictIO(text_io)
        dict_io.set(obj.to_dict())
        text_io.close()
        if self.PERMISSIONS is not None: 
            os.chmod(filename, self.PERMISSIONS)


    def delete(self, obj_to_key_func, obj): 
        if self._thread_safe and not self._i_have_lock: 
            raise DontHaveLockError()

        classkey = obj.__class__.__name__
        key = obj_to_key_func(obj)
        filename = self._filename(classkey, key)

        if not os.path.isfile(filename): 
            raise KeyError('cannot delete: \n\
                    object %s %s \n\
                    does not exist in the storage \n\
                    (file %s does not exist)' % (classkey, key, filename))

        os.remove(filename)
    



    #def load_session(session_id): 
    #    primary_key = self._session_pk(session_id)
    #    filename = self._filename('sessions', primary_key)

    #    try:
    #        text_io = io.open(filename, mode='r', encoding='utf-8')
    #    except IOError: 
    #        raise KeyError('object (%s %s) does not exist in the storage\
    #                \n(failed to open file "%s" for reading)' % primary_key)
    #    dict_io = JSONDictIO(text_io)
    #    s = Session.from_dict(dict_io.get())
    #    text_io.close()

    #    assert primary_key == self._session_pk(s)
    #    return s

    #def save_session(s): 
    #    primary_key = self._session_pk_for_session(s)
    #    filename = self._filename('sessions', primary_key)

    #    try:
    #        text_io = io.open(filename, mode='r+', encoding='utf-8')
    #    except IOError: 
    #        raise KeyError('session (primary key: %s) does not exist \
    #                (failed to open file for modification)' % primary_key)
    #    dict_io = JSONDictIO(text_io)
    #    dict_io.set(s.to_dict())
    #    text_io.close()


# TODO: add create_*, add exceptions for accessing nonexistent records
#    def _window_pk(session_id, window_id): 
#        return session_id + '.' + window_id
#
#    def _window_pk_for_window(w): 
#        return w.session_id() + '.' + w.window_id()
#
#    def load_window(session_id, window_id): 
#        primary_key = self._window_pk(session_id, window_id)
#        filename = self._filename('windows', primary_key)
#        with io.open(filename, mode='r', encoding='utf-8') as text_io: 
#            dict_io = JSONDictIO(text_io)
#            w = Window.from_dict(dict_io.get())
#        assert primary_key == self._window_pk(w)
#        return w
#
#    def save_window(w): 
#        primary_key = self._window_pk_for_window(w)
#        filename = self._filename('windows', primary_key)
#        with io.open(filename, mode='r+', encoding='utf-8') as text_io: 
#            dict_io = JSONDictIO(text_io)
#            dict_io.set(w.to_dict())
#
#
#    def _edited_file_pk(repository_path, file_path, revision): 
#        return md5(repository_path + file_path + revision)
#
#    def _edited_file_pk_for_edited_file(ef): 
#        return md5(ef.repository_path() + ef.file_path() + ef.revision())
#
#    def load_edited_file(repository_path, file_path, revision): 
#        primary_key = self._edited_file_pk(repository_path, file_path, revision)
#        filename = self._filename('edited_files', primary_key)
#        with io.open(filename, mode='r', encoding='utf-8') as text_io: 
#            dict_io = JSONDictIO(text_io)
#            ef = EditedFile.from_dict(dict_io.get())
#        assert primary_key == self._edited_file_pk(ef)
#        return ef
#
#    def save_edited_file(ef): 
#        primary_key = self._edited_file_pk_for_edited_file(ef)
#        filename = self._filename('edited_files', primary_key)
#        with io.open(filename, mode='r+', encoding='utf-8') as text_io: 
#            dict_io = JSONDictIO(text_io)
#            dict_io.set(ef.to_dict())
#
#
#    def _repository_pk(repository_id): 
#        return repository_id
#
#    def _repository_pk_for_repository(r): 
#        return r.repository_id()
#
#    def load_repository(repository_id): 
#        primary_key = self._repository_pk(repository_id)
#        filename = self._filename('repositories', primary_key)
#        with io.open(filename, mode='r', encoding='utf-8') as text_io: 
#            dict_io = JSONDictIO(text_io)
#            w = Repository.from_dict(dict_io.get())
#        assert primary_key == self._window_pk(w)
#        return w
#
#    def save_repository(r): 
#        primary_key = self._repository_pk_for_repository(r)
#        filename = self._filename('repositories', primary_key)
#        with io.open(filename, mode='r+', encoding='utf-8') as text_io: 
#            dict_io = JSONDictIO(text_io)
#            dict_io.set(r.to_dict())


#    def __init__(self, directory):
#        self._storage_dir = directory
#        self._open_objects = dict()
#
#
#    def session(self, session_id): 
#        if session_id not in self._sessions: 
#            try: 
#                self._sessions[session_id] = self._load('sessions', session_id)
#            except NotFoundException: 
#                self._sessions[session_id] = Session(session_id)
#
#        return self._sessions[session_id]
#
#
#    def window(self, window_id): 
#        if window_id not in self._windows: 
#            try: 
#                self._windows[window_id] = self._load('windows', window_id)
#            except NotFoundException: 
#                self._windows[window_id] = Window(window_id)
#
#        return self._windows[window_id]
#
#
#    def edited_file(self, repository_id, filename, revision_id): 
#        edited_file_id = self._edited_file_id(repository_id, filename, revision_id)
#
#        if edited_file_id not in self._edited_files: 
#            try: 
#                self._edited_files[edited_file_id] = self._load('edited_files', edited_file_id)
#            except NotFoundException: 
#                self._edited_files[edited_file_id] = EditedFile(repository_id, filename, revision_id)
#
#        return self._edited_files[edited_file_id]
#
#
#    def repository(self, repository_id): 
#        if repository_id not in self._repositories: 
#            try: 
#                self._repositories[repository_id] = self._load('repositories', repository_id)
#            except NotFoundException: 
#                self._repositories[repository_id] = Repository(repository_id)
#
#        return self._repositories[repository_id]
#
#
#    def close(self): 
#        for s in self._sessions: 
#            self._save_session(s)
#        for w in self._windows: 
#            self._save_window(w)
#        for ef in self._edited_files: 
#            self._save_edited_file(ef)
#        for r in self._repositories: 
#            self._save_repository(r)
#
#    def __del__(): 
#        self.close()

    #def open_object(self, object_id): 
    #    # lock object
    #    # load object
    #    if object_id not in self._open_objects: 
    #        self._open_objects[object_id] = self._load_object(object_id)
    #    return self._open_objects[object_id]
    #def close_object(self, obj): 
    #    object_id = obj.get_id()
    #    # save object
    #    # unlock object
    #    self._open_objects.remove(object_id)
    #def close(): 
    #    for obj in self._open_objects: 
    #        self.close_object(obj)

