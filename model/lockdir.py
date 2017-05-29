#!/usr/bin/env python
# -*- coding: utf8 -*-

import os
from time import sleep
from random import randint


# lock categories
RWLOCK = 'rwlock'  # exclusive lock
#TODO shared lock: READLOCK = 'readlock'


def lock(filename, lockcat, max_attempts=10, max_wait_ms=200): 

    for i in range(0, max_attempts): 
        success = attempt_lock(filename, lockcat)
        if success: 
            assert is_locked(filename, lockcat)
            assert os.path.isfile(pid_filename(filename, lockcat))
            return

        # wait before another attempt
        wait_ms = randint(0, max_wait_ms)
        wait_seconds = wait_ms / 1000.0
        sleep(wait_seconds)

    raise Exception("couldn't lock '%s' with lock category %s in %s attempts" 
            % (filename, lockcat, max_attempts))


def release(filename, lockcat): 
    if not is_locked(filename, lockcat): 
        return

    # remove the pid file, then remove the lock directory
    os.unlink(pid_filename(filename, lockcat))
    os.rmdir(lockdir_name(filename, lockcat))
    return


def attempt_lock(filename, lockcat): 
    '''Tries to lock the file. 
    Returns True if successul, False if unsuccessful.
    '''
    try: 
        os.mkdir(lockdir_name(filename, lockcat))
    except OSError: 
        # couldn't lock
        return False

    # locked successfully; put a file with my PID into the lock directory
    pid = os.getpid()
    with open(pid_filename(filename, lockcat), 'w') as f: 
        f.write('%d' % pid)
    return True


def lockdir_name(filename, lockcat): 
    '''return the name of the lock directory for the file'''
    return filename + '_' + lockcat


def pid_filename(filename, lockcat): 
    '''return the name of the lock pid file for the file'''
    return os.path.join(lockdir_name(filename, lockcat), 'pid')


def is_locked(filename, lockcat): 
    return os.path.isdir(lockdir_name(filename, lockcat))


def pid_of_lock(filename, lockcat): 
    '''return the pid of the process that has the file locked'''
    if not is_locked(filename, lockcat): 
        return None

    with open(pid_filename(filename, lockcat), 'r') as f: 
        pid = int(f.read())
    return pid

