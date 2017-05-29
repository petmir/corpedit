.PHONY: default
default: check_edit1 check_edit2 check_composed_changelog

check_edit1: edit1.patch file.txt file-after-edit1.txt
	patch file.txt edit1.patch
	if diff file.txt file-after-edit1.txt; \
		then echo '[edit1.patch OK]'; \
		else echo '[error: edit1.patch is not correct]'; \
	fi
	cp file.txt.bak file.txt  # restore original file.txt

check_edit2: edit2.patch file-after-edit1.txt file-after-edit2.txt
	patch file-after-edit1.txt edit2.patch
	if diff file-after-edit1.txt file-after-edit2.txt; \
		then echo '[edit2.patch OK]'; \
		else echo '[error: edit2.patch is not correct]'; \
	fi
	cp file-after-edit1.txt.bak file-after-edit1.txt  # restore original file-after-edit1.txt

check_composed_changelog: composed-edit1-edit2.patch file.txt file.txt.bak file-after-edit2.txt 
	patch file.txt composed-edit1-edit2.patch
	if diff file.txt file-after-edit2.txt; \
		then echo '[composed-edit1-edit2.patch OK]'; \
		else echo '[error: composed-edit1-edit2.patch is not correct]'; \
	fi
	cp file.txt.bak file.txt  # restore the original file

