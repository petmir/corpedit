#!/usr/bin/env python
# -*- coding: utf8 -*-

import pickle
import io, os

import lockdir


class DontHaveLockError(Exception): 
    def __init__(self): 
        Exception.__init__(self, 'error: you don\'t have lock (thread_safe is enabled so you need to get_lock())')


#       When locking is set to True, multiprocess safety is ensured using the lockdir module: 
#
#       * The load() method automatically locks the object's file before reading it. 
#       * The create() method locks the file before it creates it. 
#       * The delete() method releases the file after it deletes it.
#       * The save() method doesn't do anything with the lock, as it works with a locked file.
#       
#       The PickleStorage object keeps track of all its locked files and releases them 
#       when it is destructed (the __del__() method). 
#
#       The user should call the release() method on an object when no longer using it. 
#       This makes it possible to once again load() it. Calling load() on an object whose 
#       file is locked fails because it is unable to lock it.
#
#       The file being locked only prevents other processes from accessing it, 
#       not the process that created it (see "locked_by_me" in _lock_file()).
#       So the user of PickleStorage doesn't really need to care about releasing 
#       the files if the PickleStorage object only lasts for a moment. In that 
#       case it is enough that the destructor (the __del__() method) takes care 
#       of releasing the locks. 
#
#       Still, it is better to release the object as soon as it is no longer used.
#
#       An alternative to waiting for the PickleStorage object's destruction is 
#       to call its close() method. Like the destructor, it releases all the locks. 
#       After calling close(), the PickleStorage object is no longer usable.
#
class PickleStorage:
    PERMISSIONS = 0o777

    def __init__(self, directory, locking=True):
        self._storage_dir = directory
        self._closed = False

        if locking:
            self._locking = True
            self._my_locked_files = set()  # the files locked by this instance of PickleStorage
        else: 
            self._locking = False


    def storage_dir(self): 
        return self._storage_dir



    def load(self, class_, args_to_key_func, args, obj_to_key_func): 
        if self._closed:
            raise Exception('this %s object has been closed' % self.__class__.__name)

        classkey = class_.__name__
        key = args_to_key_func(**args)
        filename = self._filename(classkey, key)

        if self._locking: 
            self._lock_file(filename)  # lock the file before reading it
        try:
            text_io = io.open(filename, mode='rb')
        except IOError: 
            raise KeyError('cannot load: \n\
                    object %s %s \n\
                    does not exist in the storage \n\
                    (failed to open file "%s" for reading)' % (classkey, key, filename))
        obj = pickle.load(text_io)
        text_io.close()

        assert key == obj_to_key_func(obj)
        return obj


    def save(self, obj_to_key_func, obj): 
        if self._closed:
            raise Exception('this %s object has been closed' % self.__class__.__name)

        classkey = obj.__class__.__name__
        key = obj_to_key_func(obj)
        filename = self._filename(classkey, key)

        try:
            text_io = io.open(filename, mode='rb+')
        except IOError: 
            raise KeyError('cannot save: \n\
                    object %s %s \n\
                    does not exist in the storage \n\
                    (failed to open file "%s" for modification)' % (classkey, key, filename))
        pickle.dump(obj, text_io)
        text_io.close()


    def create(self, obj_to_key_func, obj): 
        if self._closed:
            raise Exception('this %s object has been closed' % self.__class__.__name)

        classkey = obj.__class__.__name__
        key = obj_to_key_func(obj)
        filename = self._filename(classkey, key)

        if os.path.isfile(filename): 
            raise KeyError('cannot create: \n\
                    object %s %s \n\
                    already exists in the storage \n\
                    (file %s exists)' % (classkey, key, filename))

        self._ensure_class_dir(classkey)
        if self._locking: 
            self._lock_file(filename)  # lock the file before creating it
        text_io = io.open(filename, mode='wb')
        pickle.dump(obj, text_io)
        text_io.close()
        if self.PERMISSIONS is not None: 
            os.chmod(filename, self.PERMISSIONS)


    def delete(self, obj_to_key_func, obj): 
        if self._closed:
            raise Exception('this %s object has been closed' % self.__class__.__name)

        classkey = obj.__class__.__name__
        key = obj_to_key_func(obj)
        filename = self._filename(classkey, key)

        if not os.path.isfile(filename): 
            raise KeyError('cannot delete: \n\
                    object %s %s \n\
                    does not exist in the storage \n\
                    (file %s does not exist)' % (classkey, key, filename))

        os.remove(filename)
        if self._locking: 
            self._release_file(filename)  # release the file after deleting it


    def _filename(self, classkey, objkey): 
        return self._storage_dir + '/' + classkey + '/' + objkey + '.pickle'

    def _class_dir_name(self, classkey): 
        return self._storage_dir + '/' + classkey

    def _ensure_class_dir(self, classkey): 
        class_dir = self._class_dir_name(classkey)
        if not os.path.isdir(class_dir): 
            os.mkdir(class_dir)
            if self.PERMISSIONS is not None: 
                os.chmod(class_dir, self.PERMISSIONS)
        assert os.path.isdir(class_dir)


    def release(self, obj_to_key_func, obj): 
        assert self._locking
        classkey = obj.__class__.__name__
        key = obj_to_key_func(obj)
        filename = self._filename(classkey, key)

        self._release_file(filename)

    def close(self): 
        if self._locking:
            files = self._my_locked_files.copy()
            for filename in files: 
                self._release_file(filename)

        self._closed = True

    def __del__(self): 
        if self._locking:
            files = self._my_locked_files.copy()
            for filename in files: 
                self._release_file(filename)

    def _lock_file(self, filename): 
        assert self._locking
        # if the file is locked and it is locked by this process, then allow access without locking; 
        # otherwise, lock the file
        if lockdir.is_locked(filename, lockdir.RWLOCK) and lockdir.pid_of_lock(filename, lockdir.RWLOCK) == os.getpid(): 
            locked_by_me = True
        else: 
            locked_by_me = False

        if not locked_by_me: 
            # lock the file
            lockdir.lock(filename, lockdir.RWLOCK)
            assert lockdir.is_locked(filename, lockdir.RWLOCK)
            assert lockdir.pid_of_lock(filename, lockdir.RWLOCK) == os.getpid()

            # register the filename to the set of open files so the lock can be released 
            # automatically by __del__()
            self._my_locked_files.add(filename)

    def _release_file(self, filename): 
        assert self._locking
        lockdir.release(filename, lockdir.RWLOCK)
        self._my_locked_files.remove(filename)

