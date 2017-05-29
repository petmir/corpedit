NOTE: The composed-edit1-edit2.patch file here is for the new algorithm, which is simple and great.

This is a handmade example. 

edit1.patch is a changelog that transforms file.txt into file-after-edit1.txt. 
edit2.patch is a changelog that transforms file-after-edit1.txt into file-after-edit2.txt. 
Makefile checks them.

composed-edit1-edit2.patch is a *composed* changelog made from these two: 
(a)  `diff -U 0 file.txt file-after-edit1.txt`
(b)  `diff -U 0 file.txt file-after-edit2.txt`
Applying it on a file has the same effect as applying (a), then (b).
It's like composing two mathematical functions.

To be correct, composed-edit1-edit2.patch must transform file.txt into file-after-edit2.txt.
Makefile checks this.
