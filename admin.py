#!/usr/bin/env python
# -*- coding: utf8 -*-

##################################################################################
# This is a script for administering corpedit from the command line on the server. 
#
# NOTE: It only manages the GitFileSystem, so it doesn't care when removing files 
#       if there are windows where those files are open. 
##################################################################################

import sys
from config import APP_CONFIG
from model.model import GitFileSystem, vertical_path


CMD_ADD_FILE = '--add-file'
CMD_ADD_CORPUS = '--add-corpus'
CMD_REMOVE_FILE = '--remove-file'
CMD_REMOVE_CORPUS = '--remove-corpus'

CMD_CLEAR = '--clear'
CMD_BACK_UP = '--back-up'
CMD_RESTORE = '--restore'

CMD_LIST_FILES = '--list-files'
CMD_LIST_WINDOWS = '--list-windows'
CMD_LIST_SESSIONS = '--list-sessions'

CMD_DELETE_WINDOW = '--delete-window'
CMD_DELETE_SESSION = '--delete-session'

ALL_COMMANDS = [CMD_ADD_FILE, CMD_ADD_CORPUS, CMD_REMOVE_FILE, CMD_REMOVE_CORPUS, \
        CMD_CLEAR, CMD_BACK_UP, CMD_RESTORE, \
        CMD_LIST_FILES, CMD_LIST_WINDOWS, CMD_LIST_SESSIONS, \
        CMD_DELETE_WINDOW, CMD_DELETE_SESSION]


def print_usage(commands=None): 
    print "USAGE: "

    if commands == None: 
        commands = ALL_COMMANDS
        
    if CMD_ADD_FILE in commands: 
        print ""
        print "       ./admin.py %s FILEPATH" % CMD_ADD_FILE
        print "       where FILEPATH is the path of the vertical file to be added"

    if CMD_ADD_CORPUS in commands: 
        print ""
        print "       ./admin.py %s CORPUS" % CMD_ADD_CORPUS
        print "       where CORPUS is the name of the corpus file to be added"
        print "       (or the path to its configuration file)"

    if CMD_REMOVE_FILE in commands: 
        print ""
        print "       ./admin.py %s FILEPATH" % CMD_REMOVE_FILE
        print "       where FILEPATH is the path of the vertical file to be removed"

    if CMD_REMOVE_CORPUS in commands: 
        print ""
        print "       ./admin.py %s CORPUS" % CMD_REMOVE_CORPUS
        print "       where CORPUS is the name of the corpus file to be removed"
        print "       (or the path to its configuration file)"

    if CMD_CLEAR in commands: 
        print ""
        print "       ./admin.py %s" % CMD_CLEAR
        print "       clears the runtime storage"

    if CMD_BACK_UP in commands: 
        print ""
        print "       ./admin.py %s ARCHIVE" % CMD_BACK_UP
        print "       backs up the runtime storage (where ARCHIVE is the path of "
        print "       the .tar file to back up into)"

    if CMD_RESTORE in commands: 
        print ""
        print "       ./admin.py %s ARCHIVE" % CMD_RESTORE
        print "       backs up the runtime storage (where ARCHIVE is the path of "
        print "       the .tar file to restore from)"

    if CMD_LIST_FILES in commands: 
        print ""
        print "       ./admin.py %s" % CMD_LIST_FILES
        print "       lists all files in the system"

    if CMD_LIST_WINDOWS in commands: 
        print ""
        print "       ./admin.py %s" % CMD_LIST_WINDOWS
        print "       lists all windows"

    if CMD_LIST_SESSIONS in commands: 
        print ""
        print "       ./admin.py %s" % CMD_LIST_SESSIONS
        print "       lists all sessions"

    if CMD_DELETE_WINDOW in commands: 
        print ""
        print "       ./admin.py %s WID" % CMD_DELETE_WINDOW
        print "       where WID is the window_id"

    if CMD_DELETE_SESSION in commands: 
        print ""
        print "       ./admin.py %s SID" % CMD_DELETE_SESSION
        print "       where SID is the session_id"


def add_file(file_path): 
    print 'adding file "' + file_path + '" ...'

    if GitFileSystem().has_file(file_path): 
        print '[error] the file is already present in the system: '
        print GitFileSystem().file_fspath(file_path)
        exit_code = 1
    else: 
        GitFileSystem().add_file(file_path)
        print "[OK] the file has been successfully added to the system"
        exit_code = 0

    return exit_code


def remove_file(file_path): 
    print 'removing file "' + file_path + '" ...'

    if not GitFileSystem().has_file(file_path): 
        print '[error] the file is not present in the system'
        exit_code = 1
    else: 
        GitFileSystem().remove_file(file_path)
        print "[OK] the file has been successfully removed from the system"
        exit_code = 0

    return exit_code


def vertfile(corpus_name): 
    import manatee
    corpus = manatee.Corpus(corpus_name)
    return corpus.get_conf('VERTICAL')


# module-level variables with the list of commandline arguments and the output stream
argv = None
out = None

def main():
    if len(argv) < 2: 
        print_usage()
        exit_code = 0

    elif argv[1] not in ALL_COMMANDS: 
        print_usage()
        exit_code = 1

    else:
        GitFileSystem(APP_CONFIG['gfs_dir'], 'ADMIN')

        if argv[1] == CMD_ADD_FILE: 
            if len(argv) != 3: 
                print_usage([CMD_ADD_FILE])
                exit_code = 1
            else: 
                exit_code = add_file(argv[2])

        elif argv[1] == CMD_ADD_CORPUS: 
            if len(argv) != 3: 
                print_usage([CMD_ADD_CORPUS])
                exit_code = 1
            else: 
                corpus_name = argv[2]
                file_path = vertical_path(corpus_name)
                exit_code = add_file(file_path)
                GitFileSystem().assign_corpus_name(file_path, corpus_name)

        elif argv[1] == CMD_REMOVE_FILE: 
            if len(argv) != 3: 
                print_usage([CMD_REMOVE_FILE])
                exit_code = 1
            else: 
                exit_code = remove_file(argv[2])

        elif argv[1] == CMD_REMOVE_CORPUS: 
            if len(argv) != 3: 
                print_usage([CMD_REMOVE_CORPUS])
                exit_code = 1
            else: 
                exit_code = remove_file(vertical_path(argv[2]))

        elif argv[1] == CMD_CLEAR: 
            print "not implemented yet"
            exit_code = 1

        elif argv[1] == CMD_BACK_UP: 
            print "not implemented yet"
            exit_code = 1

        elif argv[1] == CMD_RESTORE: 
            print "not implemented yet"
            exit_code = 1

        elif argv[1] == CMD_LIST_FILES: 
            files = GitFileSystem().all_files()
            print "# corpus_name : file_path : file_fspath"
            for f in files: 
                print "%s : %s : %s" \
                        % (f['corpus_name'], f['file_path'], GitFileSystem().file_fspath(f['file_path']))
            exit_code = 0

        elif argv[1] == CMD_LIST_WINDOWS: 
            print "not implemented yet"
            exit_code = 1

        elif argv[1] == CMD_LIST_SESSIONS: 
            print "not implemented yet"
            exit_code = 1

        elif argv[1] == CMD_DELETE_WINDOW: 
            print "not implemented yet"
            exit_code = 1

        elif argv[1] == CMD_DELETE_SESSION: 
            print "not implemented yet"
            exit_code = 1

        else: 
            assert False

    #sys.exit(exit_code)


def run(arg_list): 
    global argv
    argv = arg_list
    main()


if __name__ == '__main__': 
    argv = sys.argv
    main()
