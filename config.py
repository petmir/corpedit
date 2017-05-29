#!/usr/bin/env python
# -*- coding: utf8 -*-

from os.path import realpath, dirname, join
this_dir = dirname(realpath(__file__))


APP_CONFIG = {
    'storage_dir': join(this_dir, 'runtime_storage/objects'), 
    'gfs_dir': join(this_dir, 'runtime_storage/edited_files')
}
