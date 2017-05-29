.PHONY: default
default: check_c1 check_c2 check_c3 check_c4


check_c1:
	cp reference-file.txt reference-file.txt.bak 
	patch reference-file.txt c1.patch 
	if diff reference-file.txt reference-file-after-edit1.txt; \
		then echo '[c1.patch OK]'; \
		else echo '[error: c1.patch is not correct]'; \
	fi
	cp reference-file.txt.bak reference-file.txt

check_c2:
	cp reference-file-after-edit1.txt reference-file-after-edit1.txt.bak 
	patch reference-file-after-edit1.txt c2.patch 
	if diff reference-file-after-edit1.txt reference-file-after-edit2.txt; \
		then echo '[c2.patch OK]'; \
		else echo '[error: c2.patch is not correct]'; \
	fi
	cp reference-file-after-edit1.txt.bak reference-file-after-edit1.txt 

check_c3:
	cp reference-file-after-edit2.txt reference-file-after-edit2.txt.bak 
	patch reference-file-after-edit2.txt c3.patch 
	if diff reference-file-after-edit2.txt reference-file-after-edit3.txt; \
		then echo '[c3.patch OK]'; \
		else echo '[error: c3.patch is not correct]'; \
	fi
	cp reference-file-after-edit2.txt.bak reference-file-after-edit2.txt 

check_c4:
	cp reference-file-after-edit3.txt reference-file-after-edit3.txt.bak 
	patch reference-file-after-edit3.txt c4.patch 
	if diff reference-file-after-edit3.txt reference-file-after-edit4.txt; \
		then echo '[c4.patch OK]'; \
		else echo '[error: c4.patch is not correct]'; \
	fi
	cp reference-file-after-edit3.txt.bak reference-file-after-edit3.txt 


clean:
	if [ -e reference-file.txt.bak ]; \
		then cp reference-file.txt.bak reference-file.txt \
		&& rm -f reference-file.txt.bak; \
	fi
	if [ -e reference-file-after-edit1.txt.bak ]; \
		then cp reference-file-after-edit1.txt.bak reference-file-after-edit1.txt \
		&& rm -f reference-file-after-edit1.txt.bak; \
	fi
	if [ -e reference-file-after-edit2.txt.bak ]; \
		then cp reference-file-after-edit2.txt.bak reference-file-after-edit2.txt \
		&& rm -f reference-file-after-edit2.txt.bak; \
	fi
	if [ -e reference-file-after-edit3.txt.bak ]; \
		then cp reference-file-after-edit3.txt.bak reference-file-after-edit3.txt \
		&& rm -f reference-file-after-edit3.txt.bak; \
	fi
	rm -f *.index

