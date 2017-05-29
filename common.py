#!/usr/bin/env python
# -*- coding: utf8 -*-

import os
import io
import traceback
import logging
import datetime

import subprocess

this_dir = os.path.dirname(os.path.realpath(__file__))

###################################################
# --- set up global settings (done only once) --- #
###################################################

# NOTE: When running the web app, making a single action can make the app 
#       actually run multiple times (for example: visiting a page that 
#       redirects to another page; or visiting a page with AJAX). 
#       If logs are set to be cleared before each run, you will see only 
#       the log from the last run. 
#
#       So clear logs manually when running the web app.

if 'SETUP_DONE' not in globals(): 
    SETUP_DONE = True

    # [logging settings] 

    #-----------------------------------------------#
    LOG_FILE = os.path.join(this_dir, 'log/log.txt')
    if os.path.isfile(LOG_FILE): 
        #os.unlink(LOG_FILE)  # start with an empty log
        pass
    if not os.path.isfile(LOG_FILE): 
        open(LOG_FILE, 'a').close()  # create the log file
        os.chmod(LOG_FILE, 0o777)  # let everyone use the log file

    # if set to True, the output will appear in the log file immediately (no buffering)
    # (also applies to the subprocess log)
    FLUSH_LOG_IMMEDIATELY = True
    #-----------------------------------------------#

    logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)

    # Use tuples of required substrings of a stack trace line 
    # (each one begins with "File (...)", for example: 
    # 'File "segmentio.py", line 523, in compose_changelogs'
    #
    # An example tuple: ('filename\"', 'in function_name\n'), such as 
    # ('segmentio.py', 'in compose_changelogs\n').
    #
    # A call will be enabled if it has all those substrings in the stack.
    DBG_WHITELIST_ENABLED = False
    DBG_WHITELIST = [
            ('_unstaged_changes', 'parallel')#, 
            #('parallel', 'UNSTAGED')
            ]

    DBG_BLACKLIST_ENABLED = True
    DBG_BLACKLIST = [
            ('segmentio.py\"', 'in compose_changelogs\n')
            ]


    # [output settings]

    # keep this True when running the web app, otherwise the output would mess up HTTP headers
    SILENT_PROCESS_CALLS = True  
    SUBPROCESS_LOG_FILE=os.path.join(this_dir, 'log/subprocess.txt')
    if os.path.isfile(SUBPROCESS_LOG_FILE): 
        #os.unlink(SUBPROCESS_LOG_FILE)  # start with an empty log
        pass
    if not os.path.isfile(SUBPROCESS_LOG_FILE): 
        open(SUBPROCESS_LOG_FILE, 'a').close()  # create the log file
        os.chmod(SUBPROCESS_LOG_FILE, 0o777)  # let everyone use the log file

    # [whether to use the subprocess module to call external programs (it is slow)]
    PROCESS_CALLING_MODULE = 'os'
    assert PROCESS_CALLING_MODULE in ['subprocess', 'os', 'commands']


###################################################



def get_stack_trace(): 
    '''returns the current stack trace (useful for debugging with a log)'''
    stack = traceback.format_stack()
    s = u''
    for item in stack: 
        # for readability, ignore python's internal calls and calls of these debugging functions
        if not 'File "/usr' in item and \
                not 'in get_stack_trace' in item and \
                not 'get_stack_trace(' in item: 
                    #s += unicode(item)
                    s += item.decode('utf-8')
    return s


def dbg(*args): 
    '''logs the args (any number of variables), with the current stack trace'''
    if _dbg_call_enabled():
        s = u''
        for arg in args:
            s += unicode(arg)
        logging.debug(u'\n' + get_stack_trace() + u'#[' + s + u']#\n')
        if FLUSH_LOG_IMMEDIATELY: 
            flush_log()

def get_dbg(*args): 
    s = u''
    for arg in args:
        s += unicode(arg)
    return u'\n' + get_stack_trace() + u'#[' + s + u']#\n'


def dbg_notb(*args): 
    if _dbg_call_enabled():
        '''logs the args (any number of variables), without a stack trace'''
        s = u''
        for arg in args:
            s += unicode(arg)
        logging.debug(u'#[' + s + u']#\n')
        if FLUSH_LOG_IMMEDIATELY: 
            flush_log()


def subprocess_call(arg_list, verbose=False): 
    # NOTE: I used to call external programs with the subprocess module, but it is slow. See here: 
    #       https://stackoverflow.com/questions/10888846/python-subprocess-module-much-slower-than-commands-deprecated
    #       It was way too slow for setting up repositories for large files with git.
    #
    #       Since subprocess is slow and commands is deprecated, I use os.system() instead.
    #       

    with io.open(SUBPROCESS_LOG_FILE, 'a', encoding='utf-8') as splog: 
        if PROCESS_CALLING_MODULE == 'subprocess': 
            # use the slow subprocess module
            if SILENT_PROCESS_CALLS and not verbose: 
                splog.write(get_timestamp())
                splog.write(get_stack_trace())
                splog.write(u"<silent (output logged here) subprocess.call: %s>\n" % str(arg_list))
                if FLUSH_LOG_IMMEDIATELY: 
                    splog.flush()
                returncode = subprocess.call(arg_list, stdout=splog, stderr=splog)
                if returncode == 0: 
                    splog.write(u"\n")
                else: 
                    splog.write(u"(nonzero returncode: %d)\n\n" % returncode)
            else: 
                splog.write(get_timestamp())
                splog.write(get_stack_trace())
                splog.write(u"<verbose (output NOT logged here) subprocess.call: %s>\n\n" % str(arg_list))
                if FLUSH_LOG_IMMEDIATELY: 
                    splog.flush()
                returncode = subprocess.call(arg_list)
                if returncode == 0: 
                    splog.write(u"\n")
                else: 
                    splog.write(u"(nonzero returncode: %d)\n\n" % returncode)

        elif PROCESS_CALLING_MODULE == 'os': 
            # use os.system()
            splog.write(get_timestamp())
            splog.write(get_stack_trace())
            splog.write(u"<os.system: %s>\n" % str(arg_list))
            if FLUSH_LOG_IMMEDIATELY: 
                splog.flush()
            # I suppress the output by redirecting to /dev/null because os.system() writes 
            # the output to stdout so it would crash the CGI web application
            for i in range(0, len(arg_list)): 
                arg_list[i] = "'%s'" % arg_list[i]  # enclose each arg in apostrophes 
            cmd = ' '.join(arg_list) + ' >/dev/null 2>&1'
            returncode = os.system(cmd)
            if returncode == 0: 
                splog.write(u"\n")
            else: 
                splog.write(u"(nonzero returncode: %d)\n\n" % returncode)

        elif PROCESS_CALLING_MODULE == 'commands': 
            # use the commands module 
            import commands
            splog.write(get_timestamp())
            splog.write(get_stack_trace())
            splog.write(u"<commands.getstatus: %s>\n" % str(arg_list))
            if FLUSH_LOG_IMMEDIATELY: 
                splog.flush()
            for i in range(0, len(arg_list)): 
                arg_list[i] = "'%s'" % arg_list[i]  # enclose each arg in apostrophes 
            cmd = ' '.join(arg_list) + ' >/dev/null 2>&1'
            returncode = os.system(cmd)
            if returncode == 0: 
                splog.write(u"\n")
            else: 
                splog.write(u"(nonzero returncode: %d)\n\n" % returncode)

        else: 
            assert False

        if FLUSH_LOG_IMMEDIATELY: 
            splog.flush()

        assert returncode == 0
        return returncode


def flush_log(): 
    # https://stackoverflow.com/questions/13176173/python-how-to-flush-the-log-django#13753911
    logging.getLogger().handlers[0].flush()

def get_timestamp(): 
    return u"%s\n" % datetime.datetime.now()


def _dbg_call_enabled(): 
    if DBG_WHITELIST_ENABLED and DBG_BLACKLIST_ENABLED: 
        raise Exception("cannot use both blacklist and whitelist for filtering debug outputs")

    if DBG_WHITELIST_ENABLED: 
        if _call_in_whitelist(): 
            return True
        else: 
            return False

    elif DBG_BLACKLIST_ENABLED: 
        if _call_in_blacklist(): 
            return False 
        else: 
            return True

    else: 
        return True


def _call_in_whitelist(): 
    for substring_tuple in DBG_WHITELIST: 
        if _stack_matches(substring_tuple): 
            return True
        else: 
            return False

def _call_in_blacklist(): 
    for substring_tuple in DBG_BLACKLIST: 
        if _stack_matches(substring_tuple): 
            return True
        else: 
            return False

def _stack_matches(substring_tuple): 
    stack = get_stack_trace()
    for substring in substring_tuple: 
        if substring not in stack: 
            return False
    return True


##############
# source: 
# https://stackoverflow.com/questions/13250050/redirecting-the-output-of-a-python-function-from-stdout-to-variable-in-python#13250224
import StringIO, sys
from contextlib import contextmanager

@contextmanager
def redirected(out=sys.stdout, err=sys.stderr):
    saved = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        yield
    finally:
        sys.stdout, sys.stderr = saved


def fun():
    runner = InteractiveConsole()
    while True:
        out = StringIO.StringIO()
        err = StringIO.StringIO()
        with redirected(out=out, err=err):
            out.flush()
            err.flush()
            code = raw_input()
            code.rstrip('\n')
            # I want to achieve the following
            # By default the output and error of the 'code' is sent to STDOUT and STDERR
            # I want to obtain the output in two variables out and err
            runner.push(code)
            output = out.getvalue()
        print output
##############

