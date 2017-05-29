######################################################
###  data for testing segmentio.rebase_changelog   ###
######################################################

* edit1: change "first", "second" and "third" to "1st", "2nd" and "3rd"
* edit2: delete the lines with "3rd" and "fourth"; add 3 lines after "sixth"; change "ninth" to "9th"
* edit3: change "1st" to "fiRRRst"
         change "9th" to "ninEEEth" and add a line "ščřEeÉeĚěýž" below it; 
         change "nineteenth" to "ninEEEteenth"
* edit4: (...) (see c4.patch)


Data (taken from ../cN/) for testing rebasing a changelog. 

[rebaseA] rebase editX from reference-file.txt to reference-file-after-edit2.txt
================================================================================
editX-on-reference-file.patch is a changelog based on reference-file.txt. 
We're rebasing it to reference-file-after-edit2.txt. 
editX-on-reference-file-after-edit2.patch is the correct rebased changelog. 
It's the same edit, only applied to reference-file-after-edit2.txt 
instead of reference-file.txt. In other words, it applies the changelog 
editX-on-reference-file-after-edit2.patch on top of the changelog 
from reference-file.txt to reference-file-after-edit2.txt 
(that is, the changelog to new base: c12.patch).

[rebaseB] rebase editX from reference-file.txt to reference-file-after-edit4.txt
================================================================================
The same as above, only this time rebasing to reference-file-after-edit4.txt.
(changelog to new base: c1234.patch)

I used compose_changelogs() to make c12.patch and c1234.patch
=============================================================

    petr@krtek:~/fi/BP/editor/src/corpedit/model$ python
    Python 2.7.6 (default, Oct 26 2016, 20:30:19) 
    [GCC 4.8.4] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>> from segmentio import compose_changelogs, changelog_from_patch_file_content
    >>> import io
    >>> with io.open('segmentio_testdata/rebasing/c1.patch', 'r', encoding='utf-8') as f: 
    ...     c1 = changelog_from_patch_file_content(f.read())
    ... 
    >>> with io.open('segmentio_testdata/rebasing/c2.patch', 'r', encoding='utf-8') as f: 
    ...     c2 = changelog_from_patch_file_content(f.read())
    ... 
    >>> c1
    u'@@ -1,3 +1,3 @@\n-first\n-second\n-third\n+1st\n+2nd\n+3rd\n'
    >>> c2
    u'@@ -3,2 +2,0 @@\n-3rd\n-fourth\n@@ -6,0 +5,3 @@\n+ADDING\n+3\n+LINES\n@@ -9 +10 @@\n-ninth\n+9th\n'
    >>> c12 = compose_changelogs(c1, c2)
    >>> print c12
    @@ -1,4 +1,2 @@
    -first
    -second
    -third
    -fourth
    +1st
    +2nd
    @@ -6,0 +5,3 @@
    +ADDING
    +3
    +LINES
    @@ -9,1 +10,1 @@
    -ninth
    +9th

    >>> with io.open('segmentio_testdata/rebasing/c3.patch', 'r', encoding='utf-8') as f:
    ...     c3 = changelog_from_patch_file_content(f.read())
    ... 
    >>> with io.open('segmentio_testdata/rebasing/c4.patch', 'r', encoding='utf-8') as f:
    ...     c4 = changelog_from_patch_file_content(f.read())
    ... 
    >>> c123 = compose_changelogs(c12, c3)
    >>> c1234 = compose_changelogs(c123, c4)
    >>> print c1234
    @@ -1,4 +1,1 @@
    -first
    -second
    -third
    -fourth
    +1st
    @@ -7,3 +4,10 @@
    -seventh
    -eighth
    -ninth
    +LN
    +KEKščř
    +seventh
    +[éíǧhth]
    +before 9th
    +[ňiňÉÉÉth]
    +<in
    +the
    +middle>
    +ABC

    >>> 

rebases of editY
================
The same as with editX. Only editY is more tricky. There is no conflict 
but it is one line from there being a conflict -- the ranges touch but 
don't intersect. An algorithm that doesn't actually work correctly with 
the ranges will probably trip up on this.

-----------------------------------------------------------------------------------
NOTE: This stuff about the minimum distance no longer applies, as I implemented the 
      more ambitious algorithm. It passes the test on editY.

      It was actually easy to make (easier than the "shitty" algorithm that would 
      need the minimum distance).
-----------------------------------------------------------------------------------
      ((( OUTDATED
        NOTE: This is to test an algorithm that has the ambition to deal with 
              such close cases. We don't really need that. There is no problem 
              with having the limitation that there must be at least some 
              distance (like 3 lines) so that it's absolutely clear (without 
              having to deal with any complexities) that the changelog that's 
              being rebased and the changelog to the new base don't intersect.
              The users will simply have to steer clear of each other a bit. 
              They will be able to edit several lines from each other, just 
              not immediately neighboring lines. This is no problem. 
        
              --------------------------------------------------------------------
              Thus, the algorithm will only be tested on editX here. 
              And other such "easy" testdata, in segmentio_testdata/rebasing-easy.
              --------------------------------------------------------------------
        
              Let's leave editY for someone making the more ambitious variant 
              of the algorithm.
      )))

