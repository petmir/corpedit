#!/usr/bin/env python
# -*- coding: utf8 -*-

from model import model
from view.view import DATA_TYPE_PAGE, DATA_TYPE_REDIRECT, DATA_TYPE_AJAX_CONTENT, DATA_TYPE_TERMINAL_OUTPUT

from common import dbg


# TODO: use these constants (URL args names and values) everywhere they are needed (including the view), 
#       don't have it hardcoded anywhere

# URL arg names
ARG_SESSION_ID = 'username'
ARG_ACTION = 'a'
ARG_WINDOW_ID = 'wid'

ARG_SEARCH_STRING = 'search_string'

ARG_CHOOSE_FILE = 'choose_file'
ARG_FILE_PATH = 'file'
ARG_CORPUS_NAME = 'corpus'

ARG_CHOOSE_PLACE = 'choose_place'
ARG_LINE = 'line'
ARG_POS = 'pos'

ARG_SAVE_VIEWPORT_CONTENT = 'save_vp_content'  # viewport content to save, sent in an AJAX request (HTTP POST method)
ARG_BASIC_MODE = 'basic_mode'

ARG_ADMINPY_ARGS = 'args'  # NOTE: see view/admin.template


# URL arg values
ACTION_GET_HOME_PAGE = 'home'
ACTION_GET_ADMIN_PAGE = 'admin'
ACTION_DO_CLEAR_RUNTIME_STORAGE = 'clearstorage'
ACTION_DO_CLEAR_LOGS = 'clearlogs'
ACTION_DO_TEST_MANATEE = 'testmanatee'
ACTION_DO_RUN_ADMINPY = 'run_adminpy'  # NOTE: see view/admin.template

ACTION_DO_OPEN_WINDOW = 'open'
ACTION_GET_WINDOW = 'getwin'
ACTION_AJAX_GET_WINDOW = 'ajax_getwin'  # NOTE: see view/window.template
ACTION_AJAX_GET_WINDOW_FIND_BEFORE = 'ajax_getwin_find_before'  # NOTE: see view/window.template
ACTION_AJAX_GET_WINDOW_FIND_AFTER = 'ajax_getwin_find_after'  # NOTE: see view/window.template
ACTION_AJAX_GET_SUGGESTIONS = 'ajax_get_suggestions'  # NOTE: see view/autocomplete/autocomplete.js

ACTION_DO_LOCK_FILE = 'lock'
ACTION_DO_UNLOCK_FILE = 'unlock'
ACTION_DO_COMMIT_WINDOW = 'commit'

# cookie names 
COOKIE_SESSION_ID = 'session_id'  # NOTE: see view/view.py

# application configuration 
from config import APP_CONFIG


def url_for(args): 
    url = ''

    is_first_arg = True
    for a in args: 
        if is_first_arg: 
            url += '?' 
            is_first_arg = False
        else: 
            url += '&'
        url += a + '=' + args[a]

    return url


def get_home_page(): 
    # ???
    #return {'type': 'page', 'data': self.}
    return {'type': DATA_TYPE_PAGE, 'data': model.Application().home_page()}


def get_admin_page(): 
    return {'type': DATA_TYPE_PAGE, 'data': model.Application().admin_page()}

def do_clear_runtime_storage(): 
    model.Application().clear_runtime_storage()
    return {'type': DATA_TYPE_PAGE, 'data': model.Application().admin_page(msg='(info) Runtime storage cleared.')}

def do_clear_logs(): 
    model.Application().clear_logs()
    return {'type': DATA_TYPE_PAGE, 'data': model.Application().admin_page(msg='(info) Logs cleared.')}

def do_test_manatee(): 
    model.Application().test_manatee()
    return {'type': DATA_TYPE_PAGE, 'data': model.Application().admin_page(msg='(info) Manatee tested.')}

def do_run_adminpy(adminpy_args): 
    #from subprocess import check_output, CalledProcessError
    #from os.path import abspath
    #arg_list = [abspath('admin.py')] + adminpy_args.split(' ')
    #try: 
    #    adminpy_output = check_output(arg_list)
    #except CalledProcessError as e: 
    #    adminpy_output = '%s\n[%s]' % (e.output, e)

    arg_list = ['admin.py'] 
    if adminpy_args.split(' ') != ['']:
        arg_list += adminpy_args.split(' ')

    import admin
    from common import redirected
    from StringIO import StringIO
    adminpy_io = StringIO()
    with redirected(out=adminpy_io, err=adminpy_io): 
        admin.run(arg_list)
        adminpy_output = adminpy_io.getvalue()

    #print "Content-type: text/html\n\n"
    #print adminpy_output
    #import sys
    #sys.exit(0)

    return {'type': DATA_TYPE_TERMINAL_OUTPUT, 'data': {'output_text': adminpy_output}}


def do_open_window(file_path=None, corpus_name=None, pos=None, line=None, nlines=None, basic_mode=False): 
    assert file_path is None and corpus_name is not None or \
            corpus_name is None and file_path is not None

    assert pos != None or line != None
    assert not (pos != None and line != None)

    window_id = model.Application().open_window(file_path=file_path, corpus_name=corpus_name, pos=pos, line=line, nlines=nlines, basic_mode=basic_mode)
    target_args = {
            ARG_ACTION: ACTION_GET_WINDOW, 
            ARG_WINDOW_ID: window_id
            }
    return {'type': DATA_TYPE_REDIRECT, 'data': url_for(target_args)}


def get_window(window_id): 
    return {'type': DATA_TYPE_PAGE, 'data': model.Application().window_page(window_id)}


def ajax_get_window(window_id, line=None, save_viewport_content=None): 
    return {'type': DATA_TYPE_AJAX_CONTENT, 'data': model.Application().window_ajax(window_id, line, save_viewport_content)}

def ajax_get_window_find_before(window_id, line, search_string, save_viewport_content=None): 
    return {'type': DATA_TYPE_AJAX_CONTENT, 
            'data': model.Application().window_ajax_find_before(window_id, line, search_string, save_viewport_content)}

def ajax_get_window_find_after(window_id, line, search_string, save_viewport_content=None): 
    return {'type': DATA_TYPE_AJAX_CONTENT, 
            'data': model.Application().window_ajax_find_after(window_id, line, search_string, save_viewport_content)}

def ajax_get_suggestions(window_id, wordtype, word): 
    return {'type': DATA_TYPE_AJAX_CONTENT, 'data': model.Application().window_suggestions(window_id, wordtype, word)}

def do_lock_file(window_id): 
    model.Application().lock(window_id)
    target_args = {
            ARG_ACTION: ACTION_GET_WINDOW, 
            ARG_WINDOW_ID: window_id
            }
    return {'type': DATA_TYPE_REDIRECT, 'data': url_for(target_args)}
    #return get_window(window_id)

def do_unlock_file(window_id): 
    model.Application().unlock(window_id)
    target_args = {
            ARG_ACTION: ACTION_GET_WINDOW, 
            ARG_WINDOW_ID: window_id
            }
    return {'type': DATA_TYPE_REDIRECT, 'data': url_for(target_args)}

def do_commit_window(window_id): 
    model.Application().commit(window_id)
    target_args = {
            ARG_ACTION: ACTION_GET_WINDOW, 
            ARG_WINDOW_ID: window_id
            }
    return {'type': DATA_TYPE_REDIRECT, 'data': url_for(target_args)}
    #return get_window(window_id)



def run(args, cookies): 
    result = do_action(args, cookies)
    model.Application().close()
    return result

def do_action(args, cookies): 

    #if 'a' in args: 
    #    action_type = args['a']
    #else: 
    #    action_type = 'get'  # [the default action] Client (browser) is requesting the app to give some data. 
    #                         # The response will be a HTML document.

    #    #action_type = 'do'  # Client (browser) is requesting the app to do something.
    #                         # The response will be a HTTP redirect to a 'get' action to prevent 
    #                         # the user from accidentally repeating the 'do' action by going back in history.

    #    #action_type = 'ajax_get'  # Client (ajax script) is requesting the app to give some data.
    #                               # The response will be a JSON document.

    #    #action_type = 'ajax_do'  # Client (ajax script) is requesting the app to do something. 
    #                              # The response will be a JSON document (no redirect needed).

    ####


    if ARG_SESSION_ID in args:  
        # the user specified a session ID in the URL -> use it
        session_id = args[ARG_SESSION_ID]
    elif COOKIE_SESSION_ID in cookies:
        # the user didn't specify a session ID in the URL but there's a session ID in cookies -> use it
        session_id = cookies[COOKIE_SESSION_ID]
    else: 
        # there is neither -> let the application start a new session with an ID it generates
        session_id = None

    # initialize the application
    model.Application(APP_CONFIG, session_id)

    if ARG_ACTION in args: 
        action = args[ARG_ACTION]
    else: 
        action = ACTION_GET_HOME_PAGE

    #print "Content-type: text/html\n\n", '--->sid:', cookies[COOKIE_SESSION_ID]; exit()
    if action == ACTION_GET_WINDOW: 
        if ARG_WINDOW_ID in args: 
            return get_window(args[ARG_WINDOW_ID])
        else: 
            raise Exception('URL parameter %s (window id) need to be specified' % ARG_WINDOW_ID)

    # NOTE for all the AJAX actions: 
    # The request is done by Javacript in the editor window. 
    # The request is done using the HTTP POST method; viewport content (if any is being sent) is in postdata.
    # The expected response is a JSON object, not a HTML page.
    elif action == ACTION_AJAX_GET_WINDOW:
        if ARG_WINDOW_ID in args: 
            return ajax_get_window(
                    window_id=args[ARG_WINDOW_ID],
                    line=(int(args[ARG_LINE]) if (ARG_LINE in args) else None), 
                    save_viewport_content=(
                        args[ARG_SAVE_VIEWPORT_CONTENT].decode('utf-8') if (ARG_SAVE_VIEWPORT_CONTENT in args) 
                        else None))
        else: 
            raise Exception('URL parameter %s (window id) need to be specified' % ARG_WINDOW_ID)

    elif action == ACTION_AJAX_GET_WINDOW_FIND_BEFORE:
        if ARG_WINDOW_ID in args and ARG_LINE in args and ARG_SEARCH_STRING in args: 
            return ajax_get_window_find_before( 
                    window_id=args[ARG_WINDOW_ID], 
                    line=int(args[ARG_LINE]), 
                    search_string=args[ARG_SEARCH_STRING], 
                    save_viewport_content=(
                        args[ARG_SAVE_VIEWPORT_CONTENT].decode('utf-8') if (ARG_SAVE_VIEWPORT_CONTENT in args) 
                        else None)) 

    elif action == ACTION_AJAX_GET_WINDOW_FIND_AFTER:
        if ARG_WINDOW_ID in args and ARG_LINE in args and ARG_SEARCH_STRING in args: 
            return ajax_get_window_find_after( 
                    window_id=args[ARG_WINDOW_ID], 
                    line=int(args[ARG_LINE]), 
                    search_string=args[ARG_SEARCH_STRING], 
                    save_viewport_content=(
                        args[ARG_SAVE_VIEWPORT_CONTENT].decode('utf-8') if (ARG_SAVE_VIEWPORT_CONTENT in args) 
                        else None)) 

    elif action == ACTION_AJAX_GET_SUGGESTIONS:
        # NOTE: this is done using the HTTP GET method
        assert ARG_WINDOW_ID in args
        assert 'wordtype' in args
        assert 'word' in args
        return ajax_get_suggestions(window_id=args[ARG_WINDOW_ID], wordtype=args['wordtype'], word=args['word']);


    elif action == ACTION_DO_OPEN_WINDOW: 
        if ARG_BASIC_MODE in args: 
            basic_mode = True
        else: 
            basic_mode = False

        assert ARG_CHOOSE_FILE in args
        assert ARG_CHOOSE_PLACE in args

        if args[ARG_CHOOSE_FILE] == 'by_file_name': 
            assert ARG_FILE_PATH in args
            if args[ARG_CHOOSE_PLACE] == 'by_line': 
                assert ARG_LINE in args
                return do_open_window(
                        file_path=args[ARG_FILE_PATH], 
                        line=int(args[ARG_LINE]), 
                        nlines=20,  # TODO: set the number of lines dynamically based on space available for the viewport in the window
                        basic_mode=basic_mode)
            elif args[ARG_CHOOSE_PLACE] == 'by_pos': 
                assert ARG_POS in args
                return do_open_window(
                        file_path=args[ARG_FILE_PATH], 
                        pos=int(args[ARG_POS]), 
                        nlines=20,  # TODO: (as above)
                        basic_mode=basic_mode)
            else: 
                assert False

        elif args[ARG_CHOOSE_FILE] == 'by_corpus_name': 
            assert ARG_CORPUS_NAME in args
            if args[ARG_CHOOSE_PLACE] == 'by_line': 
                assert ARG_LINE in args
                return do_open_window(
                        corpus_name=args[ARG_CORPUS_NAME], 
                        line=int(args[ARG_LINE]), 
                        nlines=20,  # TODO: (as above)
                        basic_mode=basic_mode)
            elif args[ARG_CHOOSE_PLACE] == 'by_pos': 
                assert ARG_POS in args
                return do_open_window(
                        corpus_name=args[ARG_CORPUS_NAME], 
                        pos=int(args[ARG_POS]), 
                        nlines=20,  # TODO: (as above)
                        basic_mode=basic_mode)
            else: 
                assert False

        else: 
            assert False
            #raise Exception('URL parameters %s, %s, %s, %s need to be specified' 
            #        % (ARG_REPOSITORY_PATH, ARG_FILE_PATH, ARG_REVISION, ARG_LINE))


    elif action == ACTION_GET_HOME_PAGE: 
        return get_home_page()

    elif action == ACTION_GET_ADMIN_PAGE: 
        return get_admin_page()

    elif action == ACTION_DO_CLEAR_RUNTIME_STORAGE: 
        return do_clear_runtime_storage()

    elif action == ACTION_DO_CLEAR_LOGS: 
        return do_clear_logs()

    elif action == ACTION_DO_TEST_MANATEE: 
        return do_test_manatee()

    elif action == ACTION_DO_RUN_ADMINPY: 
        if ARG_ADMINPY_ARGS in args:
            return do_run_adminpy(args[ARG_ADMINPY_ARGS])
        else: 
            return do_run_adminpy('')

    elif action == ACTION_DO_LOCK_FILE: 
        if ARG_WINDOW_ID in args:
            return do_lock_file(args[ARG_WINDOW_ID])
        else: 
            raise Exception('action %s: URL parameter %s need to be specified' 
                    % (ACTION_DO_LOCK_FILE, ARG_WINDOW_ID))

    elif action == ACTION_DO_UNLOCK_FILE: 
        if ARG_WINDOW_ID in args:
            return do_unlock_file(args[ARG_WINDOW_ID])
        else: 
            raise Exception('action %s: URL parameter %s need to be specified' 
                    % (ACTION_DO_UNLOCK_FILE, ARG_WINDOW_ID))

    elif action == ACTION_DO_COMMIT_WINDOW:
        if ARG_WINDOW_ID in args:
            return do_commit_window(args[ARG_WINDOW_ID])
        else: 
            raise Exception('action %s: URL parameter %s need to be specified' 
                    % (ACTION_DO_COMMIT_WINDOW, ARG_WINDOW_ID))

    else: 
        raise Exception('invalid action: %s' % action)

    ###

    #response = dict()
    #response['type'] = "status"
    #response['data'] = {"status": action_type}

    #return response
