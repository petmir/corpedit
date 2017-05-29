* edit1: change "first", "second" and "third" to "1st", "2nd" and "3rd"
* edit2: delete the lines with "3rd" and "fourth"; add 3 lines after "sixth"; change "ninth" to "9th"
* edit3: change "1st" to "fiRRRst"
         change "9th" to "ninEEEth" and add a line "ščřEeÉeĚěýž" below it; 
         change "nineteenth" to "ninEEEteenth"
* edit4: (...) (see c4.patch)

NOTE: This is a modified version of segmentio_testdata/generated-changelog/. 
      The files (reference-file.txt, reference-file-after-edit1.txt, ...) are the same as there. 
      But each changelog (c1.patch, c2.patch, ...) represents just one edit. I made these 
      changelogs by hand (they are the same as c1,...,c4 in 
      segmentio_test.test_compose_changelogs_on_generated_changelogs() 
      and elsewhere in segmentio_test; TODO: load those from here). 
      
      Makefile checks correctness of the changelogs.

NOTE: 
    When I tried generating those changelogs (named edit1.patch, edit2.patch in
    segmentio_testdata/generated-changelog/) with -U 0 to get them without
    context lines, their hunks were made different. Then, when generating
    changelog2.patch, combinediff couldn't deal with the fact that edit2.patch
    has a hunk with src lines that overlap with dest lines of a hunk in
    changelog1.patch, in other words: it changes something that's a result of
    the changes made by the previous changelog. combinediff throws this error: 

        combinediff changelog1.patch edit2.patch > changelog2.patch
        combinediff: hunk-splitting is required in this case, but is not yet implemented
        combinediff: use the -U option to work around this
        make: *** [edit2] Error 1

    Merging with combinediff is thus definitely not good enough to suit corpedit's needs(*). 
    Because of this, I developed my own algorithm: segmentio.compose_changelogs().

    (*) NOTE: But no merging algorithm (as opposed to composition) would be good enough because 
              composition has a defined order while merging does not.
    

