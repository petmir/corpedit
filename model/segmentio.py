#!/usr/bin/env python
# -*- coding: utf8 -*-

import difflib
import tempfile
import subprocess
import os 
import string
import struct
from io import StringIO
import io
import re
import sys

sys.path.append('../')  # for imports from the project's root directory
import common
from common import dbg, dbg_notb, subprocess_call



def diff(data1, data2):
    #data1_io = io.StringIO(data1)
    #data2_io = io.StringIO(data2)
    #subprocess.check_output('diff' )
    data1_lines = data1.rstrip(os.linesep).split(os.linesep)
    data2_lines = data2.rstrip(os.linesep).split(os.linesep)

    # add a trailing newline to each line for difflib.unified_diff()
    for i in range(0, len(data1_lines)):
        data1_lines[i] += os.linesep
    for i in range(0, len(data2_lines)):
        data2_lines[i] += os.linesep

    diff_line_generator = difflib.unified_diff(data1_lines, data2_lines, n=0)  # n=0 means no context lines 
    d = u''
    for diff_line in diff_line_generator: 
        if not (diff_line.startswith('+++') or diff_line.startswith('---')): 
            d += diff_line

    return d



def patch(data, changelog): 
    # create tempfiles 
    # delete=False because we want to open them again, this time with encoding='utf-8'
    # (the tempfile module doesn't offer opening the file like that right away)
    data_tempfile = tempfile.NamedTemporaryFile(delete=False) 
    data_tempfile.close()
    with io.open(data_tempfile.name, 'w', encoding='utf-8') as data_io:
        data_io.write(data)

    changelog_tempfile = tempfile.NamedTemporaryFile(delete=False)
    changelog_tempfile.close()
    with io.open(changelog_tempfile.name, 'w', encoding='utf-8') as changelog_io: 
        changelog_io.write(changelog)

    # run the patch program
    #print "#pch", data_tempfile.name, changelog_tempfile.name
    #import traceback
    #traceback.print_stack()
    returncode = subprocess_call(["patch", data_tempfile.name, changelog_tempfile.name])

    # now, the data file contains the patched data 
    with io.open(data_tempfile.name, 'r', encoding='utf-8') as data_io:
        result = data_io.read()

    # delete the tempfiles
    #os.unlink(data_tempfile.name)
    #os.unlink(changelog_tempfile.name)
    dbg(["PATCH", data_tempfile.name, changelog_tempfile.name])

    #print "#pch:res", result
    return result


def merge_changelogs(c1, c2): 
    c1_tempfile = tempfile.NamedTemporaryFile(delete=False) 
    c1_tempfile.close()
    with io.open(c1_tempfile.name, 'w', encoding='utf-8') as c1_io:
        c1_io.write(u'--- dummyfile\n+++ dummyfile-after-c1\n')
        c1_io.write(c1)

    c2_tempfile = tempfile.NamedTemporaryFile(delete=False)
    c2_tempfile.close()
    with io.open(c2_tempfile.name, 'w', encoding='utf-8') as c2_io: 
        c2_io.write(u'--- dummyfile\n+++ dummyfile-after-c2\n')
        c2_io.write(c2)

    # run the combinediff program
    #print "#cbd", c1_tempfile.name, c2_tempfile.name
    #import traceback
    #traceback.print_stack()
    output = unicode(subprocess.check_output(["combinediff", "-U", "0", c1_tempfile.name, c2_tempfile.name]))

    # we don't want the first 3 lines (the first one beginning with "diff -u", 
    # and then the ones beginning with "---" and "+++" respectively)
    lines = output.splitlines()[3:]
    for i in range(0, len(lines)):
        lines[i] = lines[i] + '\n'
    result = string.join(lines, '')

    # delete the tempfiles
    os.unlink(c1_tempfile.name)
    os.unlink(c2_tempfile.name)

    return result



class OffsetTable: 
    def __init__(self, changelog): 
        self._hunks = get_hunks(changelog)

        self._dest_line_offset_table = []
        self._src_line_offset_table = []
        self._dest_pos_offset_table = []
        self._src_pos_offset_table = []

        for h in self._hunks: 
            # dest_line_offset
            if h.n1() != 0: 
                threshold = h.x1() + h.n1()
            else: 
                threshold = h.x1() + h.n1() + 1
            offset = h.n2() - h.n1()

            row = (threshold, offset)
            self._dest_line_offset_table.append(row)

            # src_line_offset
            if h.n2() != 0: 
                threshold = h.x2() + h.n2()
            else: 
                threshold = h.x2() + h.n2() + 1
            offset = h.n1() - h.n2()

            row = (threshold, offset)
            self._src_line_offset_table.append(row)

            # dest_pos_offset
            # TODO

            # src_pos_offset
            # TODO

    

    def _lookup(self, table, target): 
        total_offset = 0

        for row in table: 
            threshold = row[0]
            offset = row[1]

            if target >= threshold: 
                total_offset += offset
            else: 
                break

        return total_offset


    def dest_line_offset(self, src_line): 
        return self._lookup(self._dest_line_offset_table, src_line)

    def src_line_offset(self, dest_line): 
        return self._lookup(self._src_line_offset_table, dest_line)


    def dest_pos_offset(self, src_pos): 
        return self._lookup(self._dest_pos_offset_table, src_pos)

    def src_pos_offset(self, dest_pos): 
        return self._lookup(self._src_pos_offset_table, dest_pos)


def changelog_from_patch_file_content(patch_file_content): 
    lines = patch_file_content.rstrip(os.linesep).split(os.linesep)
    changelog = u''
    reached_changelog = False

    for line in lines: 
        if not reached_changelog: 
            # header lines, skip them
            if line.startswith('+++'): 
                reached_changelog = True  # the next line will be the first changelog line
        else: 
            # changelog lines
            assert line.startswith('+') or line.startswith('-') or line.startswith(' ') or \
                    line.startswith('@')
            changelog += line + os.linesep

    return changelog


def patch_file_content_from_changelog(changelog, src_filename, dest_filename): 
    patch_file_content = u''

    # header lines
    patch_file_content += '--- ' + src_filename + os.linesep
    patch_file_content += '+++ ' + dest_filename + os.linesep

    # changelog lines
    patch_file_content += changelog

    return patch_file_content


def list_of_lines(line_block): 
    '''splits a string consisting of multiple lines 
    (each one ended with \n, including the last one) 
    into a list of individual lines (each one ended with \n)'''
    assert line_block.endswith(os.linesep)
    line_list = line_block.rstrip(os.linesep).split(os.linesep) 
    for i in range(0, len(line_list)): 
        line_list[i] += os.linesep
    return line_list



def _join_neighboring_hunks_make_hunk_from_group(group): 
            # make the group of neighboring hunks into one hunk
            group_list = sorted(list(group), key=lambda hunk: (hunk.x1(), hunk.x2()))

            h_first = group_list[0]
            h_last = group_list[-1]

            # An edge contains its first line. 
            # A spike doesn't contain its first line 
            # (it's a point just below its first line).
            #
            # If the first hunk has a spike here 
            # and we're making an edge (not a spike), 
            # then we need to begin one line later 
            # (that is, just below the spike).
            if h_first.n1() == 0 and h_first.n1() != h_last.n1(): 
                assert h_first.n1() < h_last.n1()
                src_begin = h_first.x1() + 1
            else: 
                src_begin = h_first.x1()

            if h_first.n2() == 0 and h_first.n2() != h_last.n2(): 
                assert h_first.n2() < h_last.n2()
                dest_begin = h_first.x2() + 1
            else: 
                dest_begin = h_first.x2()

            ## (spiked hunks break this so don't do it this way)
            #src_end = h_last.x1() + h_last.n1()
            #src_num_lines = src_end - src_begin
            #dest_end = h_last.x2() + h_last.n2()
            #dest_num_lines = dest_end - dest_begin

            src_num_lines = 0
            dest_num_lines = 0
            for h in group_list:
                src_num_lines += h.n1()
                dest_num_lines += h.n2()

            src_content = u''
            for h in group_list: 
                src_content += u''.join(h.content_src_lines(with_minus=True))

            dest_content = u''
            for h in group_list: 
                dest_content += u''.join(h.content_dest_lines(with_plus=True))

            content = src_content + dest_content

            h = Hunk(src_begin, src_num_lines, dest_begin, dest_num_lines, content)
            return h


def _join_neighboring_hunks_src_touch(h1, h2, h1_src_is_spike, h2_src_is_spike): 
    # touch condition on src
    if h1_src_is_spike: 
        if h2_src_is_spike: 
            if h1.x1() == h2.x1(): 
                src_touch = True
            else: 
                src_touch = False
        else:
            if h1.x1() + 1 == h2.x1(): 
                src_touch = True
            else: 
                src_touch = False
    else: 
        if h2_src_is_spike: 
            if h1.x1() + h1.n1() - 1 == h2.x1(): 
                src_touch = True
            else: 
                src_touch = False
        else:
            if h1.x1() + h1.n1() == h2.x1(): 
                src_touch = True
            else: 
                src_touch = False

    return src_touch



def _join_neighboring_hunks_dest_touch(h1, h2, h1_dest_is_spike, h2_dest_is_spike): 
    # touch condition on dest
    if h1_dest_is_spike: 
        if h2_dest_is_spike: 
            if h1.x2() == h2.x2(): 
                dest_touch = True
            else: 
                dest_touch = False
        else:
            if h1.x2() + 1 == h2.x2(): 
                dest_touch = True
            else: 
                dest_touch = False
    else: 
        if h2_dest_is_spike: 
            if h1.x2() + h1.n2() - 1 == h2.x2(): 
                dest_touch = True
            else: 
                dest_touch = False
        else:
            if h1.x2() + h1.n2() == h2.x2(): 
                dest_touch = True
            else: 
                dest_touch = False

    return dest_touch


def _join_neighboring_hunks_are_neighboring(h1, h2): 
    # NOTE: h1 comes before h2

    if h1.n1() > 0: 
        # h1 has an edge on the src side
        h1_src_is_spike = False
    else: 
        # h1 has a spike on the src side
        assert h1.n1() == 0
        h1_src_is_spike = True

    if h1.n2() > 0: 
        # h1 has an edge on the dest side
        h1_dest_is_spike = False
    else: 
        # h1 has a spike on the dest side
        assert h1.n2() == 0
        h1_dest_is_spike = True

    if h2.n1() > 0: 
        # h2 has an edge on the src side
        h2_src_is_spike = False
    else: 
        # h2 has a spike on the src side
        assert h2.n1() == 0
        h2_src_is_spike = True

    if h2.n2() > 0: 
        # h2 has an edge on the dest side
        h2_dest_is_spike = False
    else: 
        # h2 has a spike on the dest side
        assert h2.n2() == 0
        h2_dest_is_spike = True

    src_touch = _join_neighboring_hunks_src_touch(h1, h2, h1_src_is_spike, h2_src_is_spike)
    dest_touch = _join_neighboring_hunks_dest_touch(h1, h2, h1_dest_is_spike, h2_dest_is_spike)

    if src_touch and dest_touch: 
        return True
    else: 
        return False


def join_neighboring_hunks(hunks): 
    '''Joins hunks that touch on both the src side and the dest side.'''

    if len(hunks) < 2: 
        return hunks

    joined_hunks = []  # the resulting list of hunks
    h1 = None
    h2 = None
    group = set()

    for i in range(0, len(hunks)): 
        if h1 is None: 
            h1 = hunks[i]
            continue  # we don't have h2 yet
        elif h2 is None: 
            h2 = hunks[i]

        #dbg_notb('i: ', i, ', h1: ((', h1, ')), h2: ((', h2, '))')
        if _join_neighboring_hunks_are_neighboring(h1, h2): 
            # h1 and h2 are neighboring
            group.add(h1)
            group.add(h2)

            #dbg_notb(u'group updated->')
            #for h in group: 
            #    dbg_notb('(', h, ')')

            if i == len(hunks) - 1: 
                # this is the last iteration -> add the group as one hunk
                h = _join_neighboring_hunks_make_hunk_from_group(group)
                joined_hunks.append(h)
                #dbg_notb(u'added group(last)->', h)
        else: 
            # h2 is not neighboring h1
            if len(group) > 0: 
                # h1 is a part of a group -> add the group as one hunk
                assert len(group) >= 2
                h = _join_neighboring_hunks_make_hunk_from_group(group)
                joined_hunks.append(h)
                #dbg_notb(u'added group->', h)
                group = set()  # start a new group
            else: 
                # h1 is alone -> add h1
                joined_hunks.append(h1)
                #dbg_notb(u'added->', h1)

            if i == len(hunks) - 1: 
                # this is the last iteration -> add h2
                joined_hunks.append(h2)
                #dbg_notb(u'added(last)->', h2)

        h1 = h2
        h2 = None  # we will get a new h2 the next iteration

    #dbg("#####")
    #for h in joined_hunks: 
    #    dbg_notb(h)
    #dbg("#####")

    return joined_hunks


def _compose_changelogs_take_c1_hunk(c1_hunks, c1_ot, c2_hunks, c2_ot, i1, i2): 
    #moves_to_c1 = []  # hunks in c1 touching the border with a spike need to be deleted, 
    #                  # and later, after neighboring hunks are joined, added to c1 in 
    #                  # a version that spans across both c1 and c2 (from c1.src to c2.dest)
    h = c1_hunks[i1]

    assert h.n2() > 0  # h has an edge along the border

    # plug the holes in c2 along the edge (one line at a time)
    for h_dest_line in range(h.x2(), h.x2() + h.n2()): 
        is_hole = True

        for c2h in c2_hunks: 
            if h_dest_line in range(c2h.x1(), c2h.x1() + c2h.n1()): 
                is_hole = False

        if is_hole: 
            # the hole is on k-th (counted from 0) dest line of h.content()
            k = h_dest_line - h.x2()  
            supplied_content = h.content_dest_lines(with_plus=False)[k]
            plug_content = '-' + supplied_content + '+' + supplied_content

            # make the plug (a one-line hunk)
            offset = c2_ot.dest_line_offset(src_line=h_dest_line)
            plug_h = Hunk(h_dest_line, 1, h_dest_line + offset, 1, plug_content)

            # insert the plug into c2
            c2_hunks.insert(0, plug_h)
            c2_hunks = sorted(c2_hunks, key=lambda hunk: hunk.x1())


    return (c1_hunks, c2_hunks)


def _compose_changelogs_take_c2_hunk(c1_hunks, c1_ot, c2_hunks, c2_ot, i1, i2): 
    #moves_to_c1 = []  # hunks in c2 touching the border with a spike need to be adjusted 
    #                  # and moved to c1 
    h = c2_hunks[i2]

    assert h.n1() > 0  # h has an edge along the border

    # plug the holes in c2 along the edge (one line at a time)
    for h_src_line in range(h.x1(), h.x1() + h.n1()): 
        is_hole = True

        for c1h in c1_hunks: 
            if h_src_line in range(c1h.x2(), c1h.x2() + c1h.n2()): 
                is_hole = False

        if is_hole: 
            # the hole is on k-th (counted from 0) src line of h.content()
            k = h_src_line - h.x1()  
            supplied_content = h.content_src_lines(with_minus=False)[k]
            plug_content = '-' + supplied_content + '+' + supplied_content

            # make the plug (a one-line hunk)
            offset = c1_ot.src_line_offset(dest_line=h_src_line)
            plug_h = Hunk(h_src_line + offset, 1, h_src_line, 1, plug_content)

            # insert the plug into c1
            c1_hunks.insert(0, plug_h)
            c1_hunks = sorted(c1_hunks, key=lambda hunk: hunk.x1())


    return (c1_hunks, c2_hunks)


def compose_changelogs(c1, c2): 
    # TODO: test it on c2->c3
    '''Let's view c1, c2 each as a function that transforms src data to dest data. 
    compose_changelogs() works as a composition of these functions: 
    c := c2 after c1
    In other words, with an argument 'data': 
    c(data) := c2(c1(data))

    NOTE: compose_changelogs() requires c1, c2 to have no context lines.
    '''

    if c1 == u'': 
        return c2
    elif c2 == u'': 
        return c1

    assert not has_context_lines(c1)
    assert not has_context_lines(c2)

    c1_hunks = get_hunks(c1)
    c1_ot = OffsetTable(c1)

    c2_hunks = get_hunks(c2)
    c2_ot = OffsetTable(c2)
    
    dbg('--- COMPOSE ---')

    # 0. Schedule treatment of c1 and c2 for all hunks that touch the border 
    #    between c1 and c2 with a spike. These hunks will be removed and later 
    #    added into c (that is, the final product: the composed changelog) 
    #    in an adjusted version.
    all_moves = []
    for i1 in range(0, len(c1_hunks)):  
        h = c1_hunks[i1]
        if h.n2() == 0: 
            # shoot the spike through c2; schedule a later deleting of the original hunk in c1
            # and then in the end, after c is finally made, adding it to c

            # NOTE: The adjusted hunk is meant to span over both c1 and c2. 
            #       If it was there during the process of joining neigboring hunks, 
            #       it would break it.
            offset = c2_ot.dest_line_offset(src_line=h.x2()+1)
            h = Hunk(h.x1(), h.n1(), h.x2() + offset, 0, h.content())
            all_moves.append({'delete_i1': i1, 'add_hunk': h})

    for i2 in range(0, len(c2_hunks)):  
        h = c2_hunks[i2]
        if h.n1() == 0: 
            # shoot the spike through c1; schedule a later deleting of the original hunk in c2
            # and then in the end, after c is finally made, adding it to c

            # NOTE: [same note as above]
            offset = c1_ot.src_line_offset(dest_line=h.x1()+1)
            h = Hunk(h.x1() + offset, 0, h.x2(), h.n2(), h.content())
            all_moves.append({'delete_i2': i2, 'add_hunk': h})


    # 1. Scheduled moves: delete the originals.
    #    (this must be done before the joining, otherwise the originals could be joined 
    #    with something)

    for i in range(0, len(all_moves)): 
        # NOTE: both true for the entire list all_moves: 
        #        * elements with delete_i2 are ordered by ascending delete_i2 and ascending add_hunk.x1()
        #        * elements with delete_i1 are ordered by ascending delete_i1 and ascending add_hunk.x2()

        if 'delete_i2' in all_moves[i]:
            # delete the hunk from c2
            dbg_notb('(delete i2 == %d)' % all_moves[i]['delete_i2'])
            c2_hunks.pop(all_moves[i]['delete_i2'])  

            # the deletion lowered by 1 the index of each following hunk in c2, 
            # so it needs to be changed in all the next moves
            for k in range(i+1, len(all_moves)): 
                if 'delete_i2' in all_moves[k]: 
                    all_moves[k]['delete_i2'] -= 1
            dbg_notb('moves updated (i2 -= 1)->', all_moves)

        elif 'delete_i1' in all_moves[i]:
            # delete the hunk from c1
            dbg_notb('(delete i1 == %d)' % all_moves[i]['delete_i1'])
            c1_hunks.pop(all_moves[i]['delete_i1'])  

            # the deletion lowered by 1 the index of each following hunk in c1, 
            # so it needs to be changed in all the next moves
            for k in range(i+1, len(all_moves)): 
                if 'delete_i1' in all_moves[k]: 
                    all_moves[k]['delete_i1'] -= 1
            dbg_notb('moves updated (i1 -= 1)->', all_moves)

        else: 
            assert False


    dbg_notb('AFTER 1. (DELETED)')
    for h in c1_hunks: 
        dbg_notb(h)
    dbg_notb('-----')
    for h in c2_hunks: 
        dbg_notb(h)
    dbg_notb('moves->', all_moves)

    # all hunks that were touching the border with a spike should be removed now
    for h in c1_hunks: 
        assert h.n2() > 0
    for h in c2_hunks: 
        assert h.n1() > 0

    # 2. Walk the border between c1 and c2, plugging holes on the other side.
    i1 = 0
    i2 = 0
    while i1 < len(c1_hunks) or i2 < len(c2_hunks):
        if i2 == len(c2_hunks): 
            # no remaining c2 hunks -> take the c1 hunk
            (c1_hunks, c2_hunks) = _compose_changelogs_take_c1_hunk(
                    c1_hunks, c1_ot, 
                    c2_hunks, c2_ot, 
                    i1, i2)

            i1 += 1

        elif i1 == len(c1_hunks): 
            # no remaining c2 hunks -> take the c2 hunk
            (c1_hunks, c2_hunks) = _compose_changelogs_take_c2_hunk(
                    c1_hunks, c1_ot, 
                    c2_hunks, c2_ot, 
                    i1, i2)

            i2 += 1

        else: 
            # take both hunks
            (c1_hunks, c2_hunks) = _compose_changelogs_take_c1_hunk(
                    c1_hunks, c1_ot, 
                    c2_hunks, c2_ot, 
                    i1, i2)

            i1 += 1

            (c1_hunks, c2_hunks) = _compose_changelogs_take_c2_hunk(
                    c1_hunks, c1_ot, 
                    c2_hunks, c2_ot, 
                    i1, i2)

            i2 += 1


    dbg_notb('AFTER 2. (PLUGGED HOLES)')
    for h in c1_hunks: 
        dbg_notb(h)
    dbg_notb('-----')
    for h in c2_hunks: 
        dbg_notb(h)


    # 3. Now, every line on the border is the same on both sides 
    #    regarding if it is in a hunk and what content it has.
    #    In both c1 and c2, join neighboring hunks.
    c1_hunks = join_neighboring_hunks(c1_hunks)
    c2_hunks = join_neighboring_hunks(c2_hunks)
    
    dbg_notb('AFTER 3. (JOINED)')
    for h in c1_hunks: 
        dbg_notb(h)
    dbg_notb('-----')
    for h in c2_hunks: 
        dbg_notb(h)


    # 4. Now, every hunk edge along the border is on both sides of it (that is, 
    #    every c1 hunk smoothly flows into a c2 hunk and every c2 hunk is smoothly 
    #    flowed into by a c1 hunk). No hunk touches the border with a spike anymore 
    #    (all the original spiked hunks from both c1 and c2 are in c1 now, and span 
    #    over both c1 and c2).
    #    Compose the changelogs.
    if len(c2_hunks) > 0:
        # there are still some hunks in c2 (if c2 contained only spiked hunk there would be none)
        c_hunks = []
        i2 = 0
        for h1 in c1_hunks: 
            dbg_notb('h1->', h1)
            assert h1.n2() > 0  # a hunk that was in c2 touching the border with a spike should NOT be here
                                # (they are added to c_hunks in the very end)
            while True: 
                assert i2 < len(c2_hunks)  # if there is a c1 hunk needing to match
                                           # a matching hunk in c2 will be found
                h2 = c2_hunks[i2]
                dbg_notb('h2->', h2)
                assert h2.n1() > 0  # there should be no hunk in c2 touching the border 
                                    # with a spike (all spiked hunks are in c1 now)
                if h1.x2() == h2.x1() and h1.n2() == h2.n1(): 
                    # found a matching one
                    i2 += 1
                    dbg_notb('(matching)')
                    break

                i2 += 1

            h1_src_content = u''.join(h1.content_src_lines())
            h2_dest_content = u''.join(h2.content_dest_lines())
            h_content = h1_src_content + h2_dest_content
            h = Hunk(h1.x1(), h1.n1(), h2.x2(), h2.n2(), h_content)
            c_hunks.append(h)
            dbg_notb('composed->', h)
    else: 
        # there are no hunks in c2
        c_hunks = c1_hunks

    dbg_notb('AFTER 4. (COMPOSED)')
    for h in c_hunks: 
        dbg_notb(h)


    # 5. Scheduled moves: add the adjusted hunks to c.
    for i in range(0, len(all_moves)): 
        # add the adjusted hunk to c
        c_hunks.append(all_moves[i]['add_hunk'])
    # put the newly added hunks in c in correct places
    c_hunks = sorted(c_hunks, key=lambda hunk: (hunk.x1(), hunk.x2()))

    dbg_notb('AFTER 5. (ADDED BACK)')
    for h in c_hunks: 
        dbg_notb(h)


    # 6. Join neighboring hunks in c.
    #    (adding the adjusted hunks could have made some neighbors)
    c_hunks = join_neighboring_hunks(c_hunks)


    c = get_changelog(c_hunks)
    return c



def invert_changelog(changelog): 
    hunks = get_hunks(changelog)

    for i in range(0, len(hunks)): 
        h = hunks[i]

        dest_lines = h.content_src_lines(with_minus=False)
        for k in range(0, len(dest_lines)): 
            dest_lines[k] = u'+' + dest_lines[k]

        src_lines = h.content_dest_lines(with_plus=False)
        for k in range(0, len(src_lines)): 
            src_lines[k] = u'-' + src_lines[k]

        content = u''.join(src_lines) + u''.join(dest_lines)

        inv_h = Hunk(x1=h.x2(), n1=h.n2(), x2=h.x1(), n2=h.n1(), content=content)
        hunks[i] = inv_h

    inv_changelog = get_changelog(hunks)
    return inv_changelog



def has_context_lines(changelog): 
    context_line_found = False
    lines = list_of_lines(changelog)
    for line in lines: 
        if not (line.startswith('+') or line.startswith('-') or line.startswith('@')): 
            context_line_found = True
            break
    return context_line_found



def rebase_changelog(changelog, to_new_base): 
    # check that there are no conflicts
    c_hunks = get_hunks(changelog)
    tnb_hunks = get_hunks(to_new_base)
    for c_h in c_hunks: 
        for tnb_h in tnb_hunks: 
            if are_conflicting_hunks(c_h, tnb_h): 
                raise Exception(u'conflict of hunk:\n' + unicode(c_h) + "with hunk:\n" + unicode(tnb_h))

    # rebase the changelog
    ot = OffsetTable(to_new_base)
    rebased_changelog = u''
    for h in c_hunks: 
        if h.n1() > 0: 
            # edge
            offset = ot.dest_line_offset(src_line=h.x1())
        else: 
            # spike
            offset = ot.dest_line_offset(src_line=h.x1()+1)

        rebased_h = Hunk(
                h.x1() + offset, h.n1(), 
                h.x2() + offset, h.n2(), 
                h.content())
        rebased_changelog += unicode(rebased_h)

    return rebased_changelog


#def _are_conflicting_hunks_src_spike(h1, h2): 
#    if h1.n1() > 0: 
#        # h1 has an edge on the src side
#        h1_src_is_spike = False
#    else: 
#        # h1 has a spike on the src side
#        assert h1.n1() == 0
#        h1_src_is_spike = True
#
#    if h2.n1() > 0: 
#        # h2 has an edge on the src side
#        h2_src_is_spike = False
#    else: 
#        # h2 has a spike on the src side
#        assert h2.n1() == 0
#        h2_src_is_spike = True
#
#    return (h1_src_is_spike, h2_src_is_spike)
#
#
#def _are_conflicting_hunks_conflict(h1, h2, h1_src_is_spike, h2_src_is_spike): 
#    if h1_src_is_spike: 
#        if h2_src_is_spike: 
#            return False
#        else: 
#            return h1.is_inside_src_range()


def are_conflicting_hunks(h1, h2): 
    h1_range = h1.src_range()
    h2_range = h2.src_range()

    h1_range_with_end_included = (h1_range[0], h1_range[1] - 1)
    h2_range_with_end_included = (h2_range[0], h2_range[1] - 1)

    return are_intersecting(h1_range_with_end_included, h2_range_with_end_included)

    #if h2.src_range()[0] < h1.src_range()[0] < h2.src_range()[1]: 
    #    # h2 begins inside h1
    #    return True
    #elif h2.src_range()[0] < h1.src_range()[1] < h2.src_range()[1]: 
    #(h1_src_is_spike, h2_src_is_spike) = _are_conflicting_hunks_src_spike(h1, h2)
    #conflict = _are_conflicting_hunks_conflict(h1, h2, h1_src_is_spike, h2_src_is_spike)
    #return conflict




def get_line_map(changelog, invert=False): 
    hunks = get_hunks(changelog)
    offset_table = OffsetTable(changelog)

    line_map = []
    current_line = 1

    for h in hunks: 
        ##print "curline: %s" % current_line
        # -- free lines before the hunk (if any) --

        #cond = lambda current_line, h: (current_line < h.x1()) if h.n1!=0 else (current_line <= h.x1())
        #if (cond): 
        #   ...
        # NOTE: don't use lambda expressions, python apparently doesn't report errors inside them 
        #       (missing parentheses after h.n1)

        if h.n1() != 0:
            if current_line < h.x1(): 
                free_lines = True
            else: 
                free_lines = False
        else: 
            if current_line <= h.x1(): 
                free_lines = True
            else: 
                free_lines = False

        if (free_lines): 
            # there are free lines before this hunk
            offset = offset_table.dest_line_offset(src_line=current_line)
            first = current_line
            last = h.x1()-1 if h.n1()!=0 else h.x1()
            ##print "sequence: %d to %d offset by %d" % (first, last, offset) 

            # type='sequences': maps a sequence to another sequence line by line 
            # (1st line to 1st line, 2nd line to 2nd line, and so on)
            item = {'type': 'sequence', 
                    'src_first': first, 'src_last': last, 
                    'dest_first': first + offset, 'dest_last': last + offset}
            line_map.append(item)

        # -- lines in the hunk --
        # type='set': maps a set to another set (nothing can be said about mapping 
        # between individual lines in the sets)

        assert not (h.n1()==0 and h.n2()==0)  # such hunk would make no sense

        if h.n1() == 0: 
            # empty src set
            item = {'type': 'addset',
                    'src_first': h.x1(), 'src_last': None, 
                    'dest_first': h.x2(), 'dest_last': h.x2() + h.n2() - 1}

        elif h.n2() == 0: 
            # empty dest set 
            item = {'type': 'removeset',
                    'src_first': h.x1(), 'src_last': h.x1() + h.n1() - 1, 
                    'dest_first': h.x2(), 'dest_last': None}

        else: 
            item = {'type': 'set',
                    'src_first': h.x1(), 'src_last': h.x1() + h.n1() - 1, 
                    'dest_first': h.x2(), 'dest_last': h.x2() + h.n2() - 1}

        line_map.append(item)
        current_line = h.x1() + (h.n1() if h.n1()!=0 else 1)

    # -- free lines from here to infinity --
    offset = offset_table.dest_line_offset(src_line=current_line)
    first = current_line
    last = sys.maxsize/2  # /2 to ensure that dest_last never overflows, even if offset is very high
    item = {'type': 'sequence', 
            'src_first': first, 'src_last': last, 
            'dest_first': first + offset, 'dest_last': last + offset}
    line_map.append(item)

    if invert:
        for i in range(0, len(line_map)): 
            # swap src and dest
            tmp_first = line_map[i]['src_first']
            tmp_last = line_map[i]['src_last']

            line_map[i]['src_first'] = line_map[i]['dest_first']
            line_map[i]['src_last'] = line_map[i]['dest_last']

            line_map[i]['dest_first'] = tmp_first
            line_map[i]['dest_last'] = tmp_last

            # in the final lines to infinity, adjust 
            # the ends (src_last, dest_last) so that src_last is sys.maxsize/2
            if line_map[i]['type'] == 'sequence' and i == len(line_map)-1: 
                offset = line_map[i]['src_last'] - sys.maxsize/2
                line_map[i]['src_last'] -= offset
                line_map[i]['dest_last'] -= offset

            # swap addset and removeset
            if line_map[i]['type'] == 'addset':
                line_map[i]['type'] = 'removeset'
            elif line_map[i]['type'] == 'removeset': 
                line_map[i]['type'] = 'addset'


    return line_map




class Segment:
    """
    """

    def __init__(self, segment_data, segment_changelog, 
            segment_src_begin_line, segment_src_end_line, 
            segment_begin_line, segment_end_line, 
            block_begin_line_in_segment, block_end_line_in_segment):
        self._is_outdated = False

        self._old_segment_data = segment_data
        self._segment_data = segment_data

        self._segment_src_begin_line = segment_src_begin_line
        self._segment_src_end_line = segment_src_end_line

        self._segment_begin_line = segment_begin_line
        self._segment_end_line = segment_end_line

        self._block_begin_line_in_segment = block_begin_line_in_segment
        self._block_end_line_in_segment = block_end_line_in_segment


    def block_data(self):
        if self._is_outdated:
            raise OutdatedSegmentException()

        segment_data_lines = self._segment_data.rstrip(os.linesep).split(os.linesep)

        block_data = u''
        for i in range(self._block_begin_line_in_segment-1, self._block_end_line_in_segment-1): 
            block_data += segment_data_lines[i] + os.linesep

        return block_data


    def set_block_data(self, new_block_data):
        if self._is_outdated:
            raise OutdatedSegmentException()

        segment_data_lines = self._segment_data.rstrip(os.linesep).split(os.linesep)
        block_data_lines = self.block_data().rstrip(os.linesep).split(os.linesep)
        new_block_data_lines = new_block_data.rstrip(os.linesep).split(os.linesep)

        # replace the block data part of the segment data

        new_segment_data = u''
        for i in range(0, self._block_begin_line_in_segment-1): 
            new_segment_data += segment_data_lines[i] + os.linesep
        for line in new_block_data_lines: 
            new_segment_data += line + os.linesep
        for i in range(self._block_end_line_in_segment-1, len(segment_data_lines)): 
            new_segment_data += segment_data_lines[i] + os.linesep

        self._segment_data = new_segment_data

        # adjust block_end_line_in_segment, segment_end_line 
        # by the change of the number of lines of the block
        num_lines_change = len(new_block_data_lines) - len(block_data_lines)
        self._block_end_line_in_segment += num_lines_change
        self._segment_end_line += num_lines_change


    def changelog(self, globalLineNumbers=False, lineNumbersFromDest=False): 
        if self._is_outdated:
            raise OutdatedSegmentException()

        ''' Returns the changelog of the segment. 

        Options for line numbers: 

        (neither option): The segment changelog's lines will be numbered from 1 
                          regardless of where the segment is. 
                          [describes changes within the segment]

        globalLineNumbers: The segment changelog will use the source of the file changelog 
                           as its source.
                           [possible to MERGE with the file changelog]

        lineNumbersFromDest: The segment changelog will use the destination of the file changelog 
                             as its source.
                           [possible to COMPOSED with the file changelog]
                        
        '''
        segment_changelog = diff(self._old_segment_data, self._segment_data)

        if globalLineNumbers: 
            hunks = get_hunks(segment_changelog, 
                    src_first_line=self._segment_src_begin_line, 
                    dest_first_line=self._segment_begin_line)
            segment_changelog = u''
            for h in hunks: 
                h.set_first_lines()  # reset the line numbers to the originals 
                segment_changelog += unicode(h)

        elif lineNumbersFromDest: 
            hunks = get_hunks(segment_changelog, 
                    src_first_line=self._segment_begin_line, 
                    dest_first_line=self._segment_begin_line)
            segment_changelog = u''
            for h in hunks: 
                h.set_first_lines()  # reset the line numbers to the originals 
                segment_changelog += unicode(h)


        return segment_changelog


    def invalidate(self): 
        # When SegmentIO saves a segment it calls this method on it. That makes the segment 
        # impossible to use. This is necessary because the file changelog has changed so 
        # the segment changelog is no longer valid. The user needs to get a new segment 
        # from SegmentIO.
        self._is_outdated = True


class OutdatedSegmentException(Exception): 
    pass


# NOTE: this is for detecting touch of a hunk with a line range
def src_touch_with_range(h, src_range): 
    # decide spike vs edge for both the hunk and the range
    if h.n1() > 0: 
        # h has an edge on the src side
        h_src_is_spike = False
    else: 
        # h has a spike on the src side
        assert h.n1() == 0
        h_src_is_spike = True

    range_n = src_range[1] - src_range[0]
    assert range_n >= 0
    if range_n > 0: 
        # src_range is an edge
        range_is_spike = False
    else: 
        # src_range is a spike
        range_is_spike = True
    range_x = src_range[0]

    # touch condition on src
    # NOTE: This was taken from _join_neighboring_hunks_src_touch. 
    #       There, the touch condition isn't correct as it didn't test for both 
    #       beginng and end touch in the case of an edge. 
    #       Here, it is fixed. 
    #       TODO: 
    #       * fix the touch condition there as well (as well as in _join_neighboring_hunks_dest_touch)
    #         [the best would be to make an universal touch condition function and use that]
    #       * test these touch functions thoroughly to make sure they always work correctly
    if h_src_is_spike: 
        if range_is_spike: 
            if h.x1() + 1 == range_x: 
                # h (a spike) and src_range (a spike) touch 
                src_touch = True
            else: 
                src_touch = False
        else:
            if h.x1() + 1 == range_x: 
                # h (a spike) touches the beginning of src_range (an edge)
                src_touch = True
            elif h.x1() + 1 == range_x + range_n: 
                # h (a spike) touches the end of src_range (an edge)
                src_touch = True
            else: 
                src_touch = False
    else: 
        if range_is_spike: 
            if h.x1() + h.n1() - 1 == range_x: 
                # src_range (a spike) touches the end of h (an edge)
                src_touch = True
            elif h.x1() - 1 == range_x: 
                # src_range (a spike) touches the beginning of h (an edge)
                src_touch = True
            else: 
                src_touch = False
        else:
            if h.x1() + h.n1() == range_x: 
                # src_range (an edge) touches the end of h (an edge)
                src_touch = True
            elif h.x1() - 1 == range_x: 
                # src_range (an edge) touches the beginning of h (an edge)
                src_touch = True
            else: 
                src_touch = False

    return src_touch


class Hunk: 
    def __init__(self, x1, n1, x2, n2, content, src_first_line=1, dest_first_line=1): 
        assert x1>=0 and n1>=0 and x2>=0 and n2>=0
        self._x1 = x1
        self._n1 = n1
        self._x2 = x2
        self._n2 = n2
        self._content = content

        self._src_first_line = src_first_line
        self._dest_first_line = dest_first_line

    def x1(self): # src begin
        return self._x1
    def n1(self): # src numlines
        return self._n1
    def x2(self): # dest begin
        return self._x2
    def n2(self): # dest num lines
        return self._n2
    def content(self): 
        return self._content

    def content_lines(self): 
        return list_of_lines(self._content)

    def content_src_lines(self, with_minus=True): 
        lines = list_of_lines(self._content)
        src_lines = []
        for line in lines: 
            if line.startswith('-'): 
                src_lines.append(line if with_minus else line[1:])
        return src_lines

    def content_dest_lines(self, with_plus=True): 
        lines = list_of_lines(self._content)
        dest_lines = []
        for line in lines: 
            if line.startswith('+'): 
                dest_lines.append(line if with_plus else line[1:])
        return dest_lines

    def header(self): 
        return "@@ -%d,%d +%d,%d @@\n" % (self._x1, self._n1, self._x2, self._n2)

    def __unicode__(self): 
        return self.header() + self._content

    def __eq__(self, other): 
        if isinstance(other, Hunk) and unicode(self) == unicode(other): 
            return True
        else: 
            return False

    def __hash__(self): 
        return hash((self._x1, self._n1, self._x2, self._n2))

    # NOTE: * these 5 methods consider the end of the range as outside the range 
    #       (like in standard python ranges)
    #       
    #       * src_range(), dest_range(), range_for_xn(): 
    #           - a range that is an edge begins with x and ends with (x + n)
    #           - a range that is a spike both begins and ends with (x + 1)
    #
    #       * is_inside_src_range(), is_inside_dest_range(): 
    #           - a spike that is touching a range (range = edge or spike) is not inside it
    def src_range(self): 
        if self._n1 > 0: 
            # edge
            return (self._x1, self._x1 + self._n1)
        else: 
            # spike
            return (self._x1 + 1, self._x1 + 1)

    def dest_range(self): 
        if self._n2 > 0: 
            # edge
            return (self._x2, self._x2 + self._n2)
        else: 
            # spike
            return (self._x2 + 1, self._x2 + 1)

    @classmethod
    def range_for_xn(cls, x, n): 
        assert x>=0 and n>=0

        if n > 0: 
            # edge
            return (x, x + n)
        else: 
            # spike
            return (x + 1, x + 1)

    def is_inside_or_touches_src_range(self, src_range): 
        if self.is_inside_src_range(src_range): 
            return True
        elif src_touch_with_range(self, src_range): 
            return True
        else: 
            return False

    def is_inside_src_range(self, src_range): 
        range_n = src_range[1] - src_range[0]
        assert range_n >= 0

        if self._n1 > 0:
            # self.src_range() is an edge
            if range_n > 0: 
                # src_range is an edge
                if self.src_range()[0] >= src_range[0] and self.src_range()[1] <= src_range[1]: 
                    return True
                else: 
                    return False
            else: 
                # src_range is a spike
                return False
        else: 
            # self.src_range() is a spike
            if range_n > 0: 
                # src_range is an edge
                if src_range[0] <= self._x1 and self._x1 + 1 < src_range[1]: 
                    return True
                else: 
                    return False
            else: 
                # src_range is a spike
                return False

    def is_inside_dest_range(self, dest_range): 
        range_n = dest_range[1] - dest_range[0]
        assert range_n >= 0

        if self._n2 > 0:
            # self.dest_range() is an edge
            if range_n > 0: 
                # dest_range is an edge
                if self.dest_range()[0] >= dest_range[0] and self.dest_range()[1] <= dest_range[1]: 
                    return True
                else: 
                    return False
            else: 
                # dest_range is a spike
                return False
        else: 
            # self.dest_range() is a spike
            if range_n > 0: 
                # dest_range is an edge
                if dest_range[0] <= self._x2 and self._x2 + 1 < dest_range[1]: 
                    return True
                else: 
                    return False
            else: 
                # dest_range is a spike
                return False


    def set_first_lines(self, src_line=1, dest_line=1):
        '''shift the line numbers of the hunk so that they are counted from a particular line'''
        src_shift = self._src_first_line - src_line
        dest_shift = self._dest_first_line - dest_line

        self._x1 += src_shift
        self._x2 += dest_shift

        self._src_first_line = src_line
        self._dest_first_line = dest_line



def get_hunks(changelog, src_first_line=None, dest_first_line=None): 
    hunks = []
    changelog_io = StringIO(changelog)
    while True: 
        line = changelog_io.readline()

        if not line: 
            break

        match = re.compile(
                '^@@ \-(?P<x1>[0-9]+)(?P<n1>(,[0-9]+)?) \+(?P<x2>[0-9]+)(?P<n2>(,[0-9]+)?) @@'
                ).match(line.rstrip(os.linesep))
        if match: 
            # old begin line
            x1 = int(match.group('x1'))  

            # old num lines
            if len(match.group('n1')) >= 2 and match.group('n1')[0]==',': 
                n1 = int(match.group('n1')[1:])
            else:
                n1 = 1  

            # new begin line 
            x2 = int(match.group('x2'))  

            # new num lines
            if len(match.group('n2')) >= 2 and match.group('n2')[0]==',': 
                n2 = int(match.group('n2')[1:])  
            else: 
                n2 = 1  

            # @@ -x1,n1 +x2,n2 @@

            # read lines until 
            # n1 lines beginning with ' ' or '-' (that is, the src lines)
            # and 
            # n2 lines beginning with ' ' or '+' (that is, the dest lines)
            # have been read
            content = ''
            num_src_lines_read = 0
            num_dest_lines_read = 0


            #dbg(n1, " ", n2, ' [', line, "]")
            while True: 
                # true if the changelog is well formed
                assert num_src_lines_read <= n1 and num_dest_lines_read <= n2  

                if num_src_lines_read == n1 and num_dest_lines_read == n2: 
                    break

                line = changelog_io.readline()

                if line[0] == ' ': 
                    num_src_lines_read += 1
                    num_dest_lines_read += 1
                elif line[0] == '-': 
                    num_src_lines_read += 1
                elif line[0] == '+': 
                    num_dest_lines_read += 1
                else: 
                    #dbg("kkk", line)
                    assert False  # error: the changelog is not well formed
                                  # (the extents in the header don't match the lines below)

                content += line

            # add the hunk to list
            h = Hunk(x1, n1, x2, n2, content, src_first_line, dest_first_line) \
                    if (src_first_line is not None and dest_first_line is not None) \
                    else Hunk(x1, n1, x2, n2, content)
            hunks.append(h)
    
    return hunks


def get_changelog(hunks): 
    changelog = u''
    for h in hunks: 
        changelog += unicode(h)
    return changelog


def begin(line_range): 
    return line_range[0]

def end(line_range):
    return line_range[1]

# NOTE: This assumes the end is still in the range (unlike in standard python range).
#       To see this, think of this example: line_range_1 = lines 5, 6
#                                           line_range_2 = lines 7, 8, 9
def are_intersecting(line_range_1, line_range_2): 
    assert begin(line_range_1) is not None \
            and end(line_range_1) is not None \
            and begin(line_range_2) is not None \
            and end(line_range_2) is not None  # don't mistakenly pass src from an addset or dest from a removeset

    return (begin(line_range_1) <= end(line_range_2) and 
            begin(line_range_2) <= end(line_range_1))


# NOTE: Likewise, this assumes that the end is still in the range (unlike in standard python range).
def is_inside(line, line_range): 
    assert isinstance(line, int) \
            and isinstance(begin(line_range), int) \
            and isinstance(end(line_range), int)


# NOTE: This works. But it doesn't make sense to have overlapping hunks 
#       in the changelog as in segmentio_testdata/handmade-changelog/reference-changelog.patch.
#       Every hunk is merged into the changelog using combinediff. The resulting changelog 
#       doesn't contain overlapping hunks even if the two changelogs (that is, the changelog 
#       and the hunk that's being merged into it) had overlapping hunks.
#
#       Therefore it can be expected that there are no overlapping hunks. This transitive stuff 
#       is not needed.
#
#       TODO: 
#       (((
#       What is needed, however, is, when *saving*, to adjust x1 of the hunk that's being saved, 
#       if other users have meanwhile saved some changes above it (that changes the line numbers).
#       )))
#       ^-- NOTE: No, this will NOT be needed. Every segment is tied to a specific revision of the 
#                 file. 
#                 A revision stays the same forever. The file is changed by creating a new revision. 
#                 [see paper notes] how to handle saving a segment of an old revision (that's what this 
#                 situation is). 
def transitive_intersect_dest(line_range, hunks):
    '''Select every hunk where line_range transitively intersects its dest range.
       NOTE: This function assumes that line_range does NOT contain its end.'''
    selected_ranges = []
    selected_hunks = []

    selected_ranges.append(line_range)
    selection_grew = True
    while selection_grew:
        selection_grew = False
        for r in selected_ranges: 
            for h in hunks: 
                r_closedend = (begin(r), end(r) - 1)  # are_intersecting() expects closed-end ranges
                h_dest_range_closedend = (begin(h.dest_range()), end(h.dest_range()) - 1)
                if are_intersecting(r_closedend, h_dest_range_closedend) and h not in selected_hunks: 
                    selected_hunks.append(h)
                    selected_ranges.append(h.dest_range())
                    selection_grew = True
    
    return selected_hunks


class LineIndex:
    # TODO: make the index sparse

    NUMBER_FORMAT = '<q'  # little-endian long long (8 bytes)
    NUMBER_SIZE = struct.calcsize(NUMBER_FORMAT)

    @classmethod
    def build(cls, src_file, index_file): 
        '''builds an index for src_file and writes it into index_file, 
        then makes a LineIndex instance from it
        '''
        # the index file contains a sequence of rows (src_line, src_pos), 
        # where src_line and src_pos are integers in binary format NUMBER_FORMAT
        with open(src_file, 'r') as src_f: 
            with open(index_file, 'wb') as ind_f: 
                line = 1
                while True:
                    pos = src_f.tell()
                    line_content = src_f.readline()
                    if not line_content: 
                        break

                    pos_packed = struct.pack(cls.NUMBER_FORMAT, pos)
                    line_packed = struct.pack(cls.NUMBER_FORMAT, line)
                    ind_f.write(line_packed)
                    ind_f.write(pos_packed)

                    line += 1

        return cls(index_file)


    def __init__(self, index_file): 
        self._index_file = index_file


    def __unicode__(self): 
        s = u'# src_line src_pos\n'
        with open(self._index_file, 'rb') as ind_f: 
            while True:
                try: 
                    row = self._read_row(ind_f)
                except EOFError: 
                    break
                s += u'%d %d\n' % row
        return s


    def index_file_name(self): 
        return self._index_file


    def _read_row(self, ind_f): 
        line_packed = ind_f.read(self.NUMBER_SIZE)
        if not line_packed: 
            raise EOFError('the whole index file has been read')
        line = struct.unpack(self.NUMBER_FORMAT, line_packed)[0]  # [0] to take the first 
                                                                  # element from the tuple

        pos_packed = ind_f.read(self.NUMBER_SIZE)
        if not pos_packed: 
            raise Exception('index file %s is badly formed' % self._index_file)
        pos = struct.unpack(self.NUMBER_FORMAT, pos_packed)[0]

        return (line, pos)


    def src_pos(self, src_line):
        # NOTE: Requires the index to be dense.
        # NOTE: You have to watch out yourself for src_pos or src_line out of range, 
        #       the index doesn't contain information about the src file's size.
        index_file_size = os.path.getsize(self._index_file)
        assert index_file_size % self.NUMBER_SIZE == 0

        target = (src_line - 1) * self.NUMBER_SIZE * 2  # lines counted from 1; 2 numbers per row
        with open(self._index_file, 'rb') as ind_f: 
            ind_f.seek(target)
            row = self._read_row(ind_f)
        return row[1]


    def src_line(self, src_pos): 
        # NOTE: Requires the index to be dense.
        # NOTE: You have to watch out yourself for src_pos or src_line out of range, 
        #       the index doesn't contain information about the src file's size.
        index_file_size = os.path.getsize(self._index_file)
        assert index_file_size % (self.NUMBER_SIZE * 2) == 0
        num_rows = index_file_size / (self.NUMBER_SIZE * 2)

        # find which row is for the line that contains src_pos
        # (algorithm based on search by halving the range)
        assert num_rows >= 1
        with open(self._index_file, 'rb') as ind_f: 
            begin = 0
            end = num_rows

            #print '>>', src_pos
            while True:
                #print '->', begin, end

                assert (end - begin) >= 1

                middle = begin + (end - begin) / 2
                target = middle * self.NUMBER_SIZE * 2  # 2 numbers per row
                ind_f.seek(target)
                middle_row = self._read_row(ind_f)  # the middle row

                if (end - begin) == 1: 
                    assert middle == begin
                    hit_row = middle_row
                    break

                before = middle - 1
                assert before >= 0
                target = before * self.NUMBER_SIZE * 2
                ind_f.seek(target)
                before_row = self._read_row(ind_f)  # the row preceding the middle row

                if (end - begin) == 2: 
                    assert middle == begin + 1
                    assert before == begin
                    if src_pos >= middle_row[1]: 
                        hit_row = middle_row
                    else: 
                        hit_row = before_row
                    break

                assert (end - begin) >= 3

                after = middle + 1
                assert after < num_rows
                target = after * self.NUMBER_SIZE * 2
                ind_f.seek(target)
                after_row = self._read_row(ind_f)  # the row following the middle row

                #print '-->', before_row, middle_row, after_row

                if src_pos < middle_row[1]: 
                    if src_pos >= before_row[1]: 
                        # found
                        hit_row = before_row
                        break
                    else: 
                        # not found yet, it's somewhere above before_row
                        end = before
                        if begin + 1 == end: 
                            # there is only one row above before_row
                            target = begin * self.NUMBER_SIZE * 2
                            ind_f.seek(target)
                            hit_row = self._read_row(ind_f)
                            break
                        # continue the cycle...

                elif src_pos >= middle_row[1]: 
                    if src_pos < after_row[1]: 
                        # found
                        hit_row = middle_row
                        break
                    else: 
                        # not found yet, it's somewhere below middle_row
                        begin = middle + 1
                        assert begin < end
                        if begin + 1 == end: 
                            # there is no row below middle_row
                            hit_row = middle_row
                            break
                        # continue the cycle...

        #print hit_row
        return hit_row[0]


class LineReadIO: 
    def read_lines(self, line, num_lines): 
        raise NotImplementedError()

    def find_before(self, current_line, search_string, max_search_length): 
        '''Find the first line before current_line that contains search_string. 
        Only goes through max_search_length lines, then ends the search.
        Returns -1 if the line is not found.
        '''
        raise NotImplementedError()

    def find_after(self, current_line, search_string, max_search_length): 
        '''Find the first line after current_line that contains search_string. 
        Only goes through max_search_length lines, then ends the search.
        Returns -1 if the line is not found.
        '''
        # TODO: limit with the length of file in lines (here and elsehere as well!)
        raise NotImplementedError()


class FileLineReadIO(LineReadIO): 
    def __init__(self, file_io, index=None): 
        self._file_io = file_io
        self._index = index

    def read_lines(self, line, num_lines): 
        dbg("reading physical lines l:", line, ",n:", num_lines, " of IO ", self._file_io)
        dbg(self._file_io)

        if self._index is None: 
            # find the line by reading and counting the lines before it 
            # (linear complexity, slow)
            self._file_io.seek(0)
            for i in range(1, line): 
                self._file_io.readline()

        else: 
            # find the line by using the index 
            # (logarithmic complexity, very fast even for extremely large files)
            dbg("using index file ", self._index.index_file_name())
            pos = self._index.src_pos(src_line=line)
            dbg("from the index: line ", line, " begins on pos ", pos)
            self._file_io.seek(pos)

        data = u''

        for i in range(0, num_lines): 
            data += self._file_io.readline()

        return data


    def line_containing_pos(self, pos): 
        if self._index is None: 
            self._file_io.seek(0)
            line = 1
            while True:
                # TODO debug this for edge cases (empty file, pos at the very end, ...)
                self._file_io.readline()

                reached_pos = self._file_io.tell()
                if pos <= reached_pos: 
                    break
                line += 1

            return line

        else: 
            dbg("(getting line for pos) using index file ", self._index.index_file_name())
            line = self._index.src_line(src_pos=pos)
            dbg("from the index: pos ", pos, " is on line ", line)
            return line


    def find_before(self, current_line, search_string, max_search_length=100): 
        line = current_line - 1
        while line >= 1: 
            if current_line - line > max_search_length: 
                break
            line_content = self.read_lines(line, 1)
            if search_string in line_content: 
                return line
            line -= 1

        return -1


    def find_after(self, current_line, search_string, max_search_length=100): 
        line = current_line + 1
        while True: 
            if line - current_line > max_search_length: 
                break
            line_content = self.read_lines(line, 1)
            if search_string in line_content: 
                return line
            line += 1

        return -1




class SegmentIO(LineReadIO):
    def __init__(self, line_read_io, changelog): 
        self._line_read_io = line_read_io
        self._changelog = changelog

    def get_segment(self, block_begin_line, block_num_lines): 
        block_end_line = block_begin_line + block_num_lines
        block_line_range = (block_begin_line, block_end_line)

        # Legend: 
        # B: block line range 
        # S: segment line range 
        # S_src: segment src line range

        # get the segment_hunks
        segment_hunks = self._get_segment_hunks(block_line_range)

        # B -> S
        segment_line_range = self._get_segment_line_range(block_line_range, segment_hunks)

        # S -> {beginBinS, endBinS}
        block_begin_line_in_segment = block_line_range[0] - segment_line_range[0] + 1  # lines are counted from 1 
        block_end_line_in_segment = block_line_range[1] - segment_line_range[0] + 1

        # S -> S_src
        segment_src_line_range = self._get_segment_src_line_range(segment_line_range, block_line_range, 
                segment_hunks)

        # get the segment changelog
        segment_changelog = self._get_segment_changelog(segment_src_line_range, segment_line_range, 
                segment_hunks)

        # load the segment src data from the file
        dbg("getting segment <dest ", segment_line_range, ", src ", segment_src_line_range, ">", 
                " from SegmentIO on LRIO ", self._line_read_io)
        segment_orig_data = self._read_src_lines(segment_src_line_range)

        # apply the segment changelog
        segment_data = patch(segment_orig_data, segment_changelog)

        # return the segment
        segment = Segment(segment_data, segment_changelog, 
                    segment_src_line_range[0], segment_src_line_range[1], 
                    segment_line_range[0], segment_line_range[1], 
                    block_begin_line_in_segment, block_end_line_in_segment)

        dbg("got segment <dest ", segment_line_range, ", src ", segment_src_line_range, ">", 
                " from SegmentIO on LRIO ", self._line_read_io, 
                "\n -> block_data: \n", segment.block_data(), 
                "\n -> segment_data: \n", segment_data, 
                "\n -> segment_orig_data: \n", segment_orig_data)

        return segment


    def save_segment(self, segment): 
        segment_changelog_lnd = segment.changelog(lineNumbersFromDest=True)
        self._changelog = compose_changelogs(self._changelog, segment_changelog_lnd)
        segment.invalidate()

    def file_changelog(self): 
        return self._changelog


    def _get_segment_hunks(self, block_line_range): 
        # find out which hunks the block line range intersects with
        all_hunks = get_hunks(self._changelog)
        segment_hunks = transitive_intersect_dest(block_line_range, all_hunks)
        return segment_hunks


    def _get_segment_line_range(self, block_line_range, segment_hunks): 
        # find the smallest range encompassing all of the segment hunks
        # NOTE: 
        #   There must be no overlapping hunks. With an overlapping hunk (in [*]), it broke: 
        #   it failed to take into account that the last hunk changed the length of 
        #   the previous hunk. 
        #   [*] segmentio_testdata/handmade-changelog/reference-changelog.patch.old
        min = sys.maxint
        max = 0
        for h in segment_hunks: 
            #print 'hunk--->', h.header().rstrip(), h.dest_range()
            if h.dest_range()[0] < min: 
                min = h.dest_range()[0]
            if h.dest_range()[1] > max: 
                max = h.dest_range()[1]

        # the segment line range must contain the entire block range
        if min > block_line_range[0]: 
            min = block_line_range[0]
        if max < block_line_range[1]: 
            max = block_line_range[1]

        # this is the segment line range
        return (min, max)
            


    def _get_segment_src_line_range(self, segment_line_range, block_line_range, segment_hunks):
        #all_hunks = get_hunks(self._changelog)
        #
        ## -- get hunks of the segment --
        #segment_hunks = []
        #for h in all_hunks: 
        #    if h.is_inside_dest_range(segment_line_range): 
        #        segment_hunks.append(h)

        if segment_hunks == []: 
            # the segment is entirely made of free lines (that is, it contains no hunks)
            ot = OffsetTable(self._changelog)

            begin = segment_line_range[0]
            src_begin = begin + ot.src_line_offset(dest_line=begin)

            end = segment_line_range[1]
            src_end = end + ot.src_line_offset(dest_line=end)

            # this is the segment src line range
            return (src_begin, src_end)

        else: 
            # the segment contains at least one hunk

            # -- get the smallest src range containing all the hunks of the segment --
            min = sys.maxint
            max = 0
            for h in segment_hunks: 
                if h.src_range()[0] < min: 
                    min = h.src_range()[0]
                if h.src_range()[1] > max: 
                    max = h.src_range()[1]

            # -- pad it with block lines before and after --

            # get the smallest dest range containing all the hunks of the segment
            dest_min = sys.maxint
            dest_max = 0
            for h in segment_hunks: 
                if h.dest_range()[0] < dest_min: 
                    dest_min = h.dest_range()[0]
                if h.dest_range()[1] > dest_max: 
                    dest_max = h.dest_range()[1]

            if block_line_range[0] < dest_min: 
                # the block begins before the dest of the first hunk of the segment
                num_lines_before = dest_min - block_line_range[0]
            else: 
                # the block begins at the same time as the dest of the first hunk of the segment
                num_lines_before = 0

            if dest_max < block_line_range[1]: 
                # the block ends after the dest of the last hunk of the segment
                num_lines_after = block_line_range[1] - dest_max
            else: 
                # the block ends at the same time as the dest of the last hunk of the segment
                num_lines_after = 0

            min -= num_lines_before
            max += num_lines_after

            # this is the segment src line range
            return (min, max)

    
    def _get_segment_changelog(self, segment_src_line_range, segment_line_range, segment_hunks):
        #all_hunks = get_hunks(self._changelog)
        #segment_changelog = u''
        #for h in all_hunks: 
        #    print '-->', unicode(h)
        #    print '-->', segment_src_line_range
        #    if h.is_inside_src_range(segment_src_line_range):# or \
        #        #    (h.n1()==0 and h.is_inside_or_touches_src_range(segment_src_line_range)): # NOTE this line fixes crash_1
        #        h.set_first_lines(segment_src_line_range[0], segment_line_range[0])
        #        segment_changelog += h.header()
        #        segment_changelog += h.content()

        segment_changelog = u''
        for h in segment_hunks: 
            h.set_first_lines(segment_src_line_range[0], segment_line_range[0])
            segment_changelog += h.header()
            segment_changelog += h.content()

        return segment_changelog


    def _read_src_lines(self, src_line_range): 
        dbg("reading src line range ", src_line_range ," of SegmentIO on LRIO ", self._line_read_io)

        num_lines = end(src_line_range) - begin(src_line_range)
        return self._line_read_io.read_lines(begin(src_line_range), num_lines)


    # implements LineReadIO
    def read_lines(self, line, num_lines): 
        dbg("reading dest lines l:", line, ",n:", num_lines ," of SegmentIO on LRIO ", self._line_read_io)

        seg = self.get_segment(block_begin_line=line, block_num_lines=num_lines)
        return seg.block_data()

    def find_before(self, current_line, search_string, max_search_length=100): 
        line = current_line - 1
        while line >= 1: 
            if current_line - line > max_search_length: 
                break
            seg = self.get_segment(block_begin_line=line, block_num_lines=1)
            line_content = seg.block_data()
            if search_string in line_content: 
                return line
            line -= 1

        return -1

    def find_after(self, current_line, search_string, max_search_length=100): 
        line = current_line + 1
        while True: 
            if line - current_line > max_search_length: 
                break
            seg = self.get_segment(block_begin_line=line, block_num_lines=1)
            line_content = seg.block_data()
            if search_string in line_content: 
                return line
            line += 1

        return -1



#    def _offset_of_orig_line(self, line_in_file): 
#
#        # get offset from index
#
#    def _get_line_in_file(self, line): 
#        # 1. add change of number of lines of every hunk (= diff change of sequence of lines) 
#        # 2. if this line is in a hunk: 
#        #        add the change of number of lines before it
#        pass
#
#    def _read_line(self, line): 
#        # NOTE: In a file that's been changed, only one line at a time can be read.
#        #       The number of the next line needs to be adjusted again as there 
#        #       could be deleted lines or added lines(!) in between.
#
#        # translate the line number to the line number in the real file
#        line_in_file = self._get_line_in_file(line)
#
#        # Shift line numbers in the changelog so that line number 1 is for the 
#        # first line of the segment (not the file).
#        #
#        # * hunks for lines before the segment will for "@@ -x,9 +1,10 @@" have x<0 and be scrapped
#        # * hunks for lines after the segment will for "@@ -x,9 +1,10 @@" x>num_lines and be scrapped
#        #
#        # So 
#        segment_changelog = self._get_shifted_changelog(line_in_file)
#
#        # get offset in the real file from the index (TODO)
#        offset = self._get_offset_of_line(line_in_file)
#
#
#        # read the original content of the line from the file
#
#        self._file_io.seek(offset)
#        orig_content = self._file_io.readline()
#
#        # get the new content of the line the applying the changelog
#        content = self._patch(orig_)
#
#        return content
#
#
#    def set_segment_content(self, line, current_content, new_content): 
#        pass
#        # current_content := get_segment_content(
#        # merge diff(current_content, new_content) adjusted by line with changelog
#        # done; from now, get_segment_content() will pretend the new content is there
#        # NOTE: 
#        # current_content can be outdated: 
#        # (a) current_content is outdated with regards to changelog (scenarios Sa1, Sa2): 
#        #              The merge of diff(current_content, new_content) adjusted by line with changelog
#        #              will fail because of conflict.
#        #        _____________________________________________________________________________________
#        #
#        #        (Sa1)  Let: user U
#        #              1.  U opens a segment (s1) in a window.
#        #              2.  U opens another segment (s2) that is in the same place (i.e. shares 
#        #                  some lines with s1) in another window (w2).
#        #              3.  U switches to w1 and edits s1. The edit is not[fs!] yet saved in the changelog.
#        #              4.  [fl!] U switches to w2 amd edits s2. Then moves one line up. That saves  
#        #                  the edit of s2 in the changelog.
#        #              5.  U switches to w1 and moves one line up. That saves the edit of s1 in the 
#        #                  changelog with outdated current_content (it doesn't contain the edit of s2).
#        #
#        #        (Sa2)  Let: user U
#        #               1.  U opens a segment (s1) in a window.
#        #               2.  U opens another segment (s2) that is in the same place (i.e. shares 
#        #                   some lines with s1) in another window (w2).
#        #               3.  U switches to w1 and edits s1. Then moves one line up. That saves  
#        #                   the edit of s1 in the changelog.
#        #               4.  [fl!] U switches to w2 and edits s2. Then moves one line up. That saves 
#        #                   the edit of s2 in the changelog with outdated current_content (it 
#        #                   doesn't contain the edit of s1).
#        #
#        #        (analysis)
#        #         [fs!] = fault of saving 
#        #         [fl!] = fault of loading 
#        #         => solution: Save on blur (prevents [fs!]), load on focus (prevents [fl!]).
#        #
#        # (b) current_content is outdated with regards to the file itself (scenario Sb1): 
#        #              The merge 
#        # 
#        #        _____________________________________________________________________________________
#        #
#        #        (Sb1)  Let: users U1, U2
#        #              1.  U1 opens a segment (s1) in a file.
#        #              2.  U1 begins editing, doesn't move the viewport for a long time. 
#        #              3.  U2 opens a segment (s2) in the same file in the same place (i.e. shares 
#        #                  some lines with s1), edits it and commits.
#        #   TODO       4. U1 moves up and loads from the commited stuff, U1's changelog 
#        #                 is not applicable on it, therefore the load fails.
#        #
#        #         solution: cheap substitute for conflict resolution UI
#        #      
#        #
#        # In both cases (a) and (b), the conflict is only with the segment that is currently open 
#        # in the user's viewport.  
#        #
#        # In a multiuser environment, there can also be case where changed segments that 
#        # are not currently opened in a viewport (they only exist as parts of the file's 
#        # changelog) are in conflict with the file (TODO scenario Sm). That is, the 
#        # "minus" lines in the changelog are outdated with regards to the file.
#        #
#        # Solving this case would require to create an illusion that the user is editing 
#        # a local copy of the file. A way to "solve" that: change the "minus" lines from 
#        # the changelog to the correspoding (based on line number?!) lines from the file. 
#        # That would be unsafe, just as if when saving a segment, there was no current_content 
#        # (that is, the original content of the segment when it was loaded into the viewport) 
#        # and the original content (to diff with the new content) was loaded straight from the 
#        # file. The reason is, an edit is defined not only by its destination (the "plus" lines)  
#        # but also a source (the "minus" lines). If someone else (be it the same user in another 
#        # window or another user by commiting) changes the place in the file so that the "minus" 
#        # lines of the edit are outdated, the edit is no longer valid and the user must be 
#        # notified of that.
#        #
#
#        ## overwrites everything with a dict
#        #self._io.seek(0)
#        #self._io.truncate()
#        #json_string = unicode(json.JSONEncoder().encode(d))
#        #self._io.write(json_string)

