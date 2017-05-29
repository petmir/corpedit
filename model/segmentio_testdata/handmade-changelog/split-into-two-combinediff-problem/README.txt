NOTE: After I split the last hunk off to a separate patch file I adjusted its x1.
      This is because it's now applied *after* the first patch file so the src 
      line numbers it works with are different (already changed by the first patch file).
      Such adjustment would need to be done when merging a hunk into the changelog 
      if other users have meanwhile merged their changes (while I was editing).

NOTE2: combinediff only merges these overlapping hunks when invoked with -U 0, 
       that is, generating output without context lines. That's OK with me.

           petr@krtek:~/tmp$ cp file-orig.txt file.txt
           petr@krtek:~/tmp$ patch file.txt ref.patch 
           patching file file.txt
           petr@krtek:~/tmp$ combinediff ref.patch ref2.patch > combined.patch
           combinediff: hunk-splitting is required in this case, but is not yet implemented
           combinediff: use the -U option to work around this
           petr@krtek:~/tmp$ man combinediff
           petr@krtek:~/tmp$ combinediff -U 3 ref.patch ref2.patch > combined.patch
           combinediff: hunk-splitting is required in this case, but is not yet implemented
           combinediff: use the -U option to work around this
           petr@krtek:~/tmp$ combinediff -U 5 ref.patch ref2.patch > combined.patch
           combinediff: hunk-splitting is required in this case, but is not yet implemented
           combinediff: use the -U option to work around this
           petr@krtek:~/tmp$ combinediff -U 2 ref.patch ref2.patch > combined.patch
           combinediff: hunk-splitting is required in this case, but is not yet implemented
           combinediff: use the -U option to work around this
           petr@krtek:~/tmp$ combinediff -U 0 ref.patch ref2.patch > combined.patch
           petr@krtek:~/tmp$ 
