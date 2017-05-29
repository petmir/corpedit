#!/usr/bin/env python
# -*- coding: utf8 -*-

import unittest
import lockdir

import os
import shutil


class LockdirModuleTestCase(unittest.TestCase): 
    #def _cleanup(self): 
    #    shutil.rmtree('lockdir_testdata/a.txt_rwlock')
    #def setUp(self): 
    #    self._cleanup()

    def test_basic_scenario_only_me(self): 
        fileA = 'lockdir_testdata/a.txt'
        self.assertTrue(os.path.isfile(fileA))
        #self.assertFalse(lockdir.is_locked(fileA, lockdir.RWLOCK))

        # lock the file
        lockdir.lock(fileA, lockdir.RWLOCK)

        # check that the file is locked and that the PID is my PID
        self.assertTrue(lockdir.is_locked(fileA, lockdir.RWLOCK))
        self.assertEqual(lockdir.pid_of_lock(fileA, lockdir.RWLOCK), os.getpid())

        # Try to lock the file again, it should run out of attempts and fail. 
        # The file already locked and there is only me (this process) so nobody 
        # will release the lock meanwhile.
        with self.assertRaises(Exception): 
            lockdir.lock(fileA, lockdir.RWLOCK)

        # release the lock
        lockdir.release(fileA, lockdir.RWLOCK)
        self.assertFalse(lockdir.is_locked(fileA, lockdir.RWLOCK))


if __name__ == '__main__': 
    unittest.main()
