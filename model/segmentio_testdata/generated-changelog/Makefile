.PHONY: default
default: edit3 test3


# NOTE: 
# The "|true" after each diff is there to make the exit status 0.
# Otherwise the make would stop after the first diff command with 
# "make: *** [all] Error 1" 
# because diff returns 1 if the files are different.
edit1:
	touch changelog0.patch
	cp reference-file.txt file.txt
	cp reference-file-after-edit1.txt file-after-edit.txt
	diff -u file.txt file-after-edit.txt > edit1.patch | true
	combinediff changelog0.patch edit1.patch > changelog1.patch

edit2: edit1
	cp reference-file-after-edit1.txt file.txt
	cp reference-file-after-edit2.txt file-after-edit.txt
	diff -u file.txt file-after-edit.txt > edit2.patch | true
	combinediff changelog1.patch edit2.patch > changelog2.patch

edit3: edit2
	cp reference-file-after-edit2.txt file.txt
	cp reference-file-after-edit3.txt file-after-edit.txt
	diff -u file.txt file-after-edit.txt > edit3.patch | true
	combinediff changelog2.patch edit3.patch > changelog3.patch

test3: 
	cp reference-file.txt test3.txt
	patch test3.txt changelog3.patch
	if diff test3.txt reference-file-after-edit3.txt; then echo "test of changelog3 OK"; else echo "test of changelog3 failed!"; fi


clean:
	rm -f file.txt file-after-edit.txt \
		edit1.patch edit2.patch edit3.patch \
		changelog0.patch changelog1.patch changelog2.patch changelog3.patch \
		test3.txt

