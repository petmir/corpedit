.PHONY: default
default: check_c1 check_c2 check_c3 check_c4 check_c12 check_c1234 try_eXrA try_eXrB try_eYrA try_eYrB


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

check_c12:
	cp reference-file.txt reference-file.txt.bak 
	patch reference-file.txt c12.patch 
	if diff reference-file.txt reference-file-after-edit2.txt; \
		then echo '[c12.patch OK]'; \
		else echo '[error: c12.patch is not correct]'; \
	fi
	cp reference-file.txt.bak reference-file.txt

check_c1234:
	cp reference-file.txt reference-file.txt.bak 
	patch reference-file.txt c1234.patch 
	if diff reference-file.txt reference-file-after-edit4.txt; \
		then echo '[c1234.patch OK]'; \
		else echo '[error: c1234.patch is not correct]'; \
	fi
	cp reference-file.txt.bak reference-file.txt

try_eXrA: 
	# [editX, rebaseA] 
	# test if the rebased version of editX works 
	# (rebase from from reference-file.txt to reference-file-after-edit2.txt)
	cp reference-file-after-edit2.txt reference-file-after-edit2.txt.bak 
	if patch reference-file-after-edit2.txt editX-on-reference-file-after-edit2.patch; \
		then echo "[editX-on-reference-file-after-edit2.patch is applicable, possibly OK \n -> check reference-file-after-edit2-editX.txt to see if it did the right thing]"; \
		else echo '[error: editX-on-reference-file-after-edit2.patch is not applicable]'; \
	fi
	cp reference-file-after-edit2.txt reference-file-after-edit2-editX.txt
	cp reference-file-after-edit2.txt.bak reference-file-after-edit2.txt 

try_eXrB: 
	# [editX, rebaseB] 
	# test if the rebased version of editX works 
	# (rebase from from reference-file.txt to reference-file-after-edit4.txt)
	cp reference-file-after-edit4.txt reference-file-after-edit4.txt.bak 
	if patch reference-file-after-edit4.txt editX-on-reference-file-after-edit4.patch; \
		then echo "[editX-on-reference-file-after-edit4.patch is applicable, possibly OK \n -> check reference-file-after-edit4-editX.txt to see if it did the right thing]"; \
		else echo '[error: editX-on-reference-file-after-edit4.patch is not applicable]'; \
	fi
	cp reference-file-after-edit4.txt reference-file-after-edit4-editX.txt
	cp reference-file-after-edit4.txt.bak reference-file-after-edit4.txt 

try_eYrA: 
	# [editY, rebaseA]
	# test if the rebased version of editY works 
	# (rebase from from reference-file.txt to reference-file-after-edit2.txt)
	cp reference-file-after-edit2.txt reference-file-after-edit2.txt.bak 
	if patch reference-file-after-edit2.txt editY-on-reference-file-after-edit2.patch; \
		then echo "[editY-on-reference-file-after-edit2.patch is applicable, possibly OK \n -> check reference-file-after-edit2-editY.txt to see if it did the right thing]"; \
		else echo '[error: editY-on-reference-file-after-edit2.patch is not applicable]'; \
	fi
	cp reference-file-after-edit2.txt reference-file-after-edit2-editY.txt
	cp reference-file-after-edit2.txt.bak reference-file-after-edit2.txt 

try_eYrB: 
	# [editY, rebaseB]
	# test if the rebased version of editY works 
	# (rebase from from reference-file.txt to reference-file-after-edit4.txt)
	cp reference-file-after-edit4.txt reference-file-after-edit4.txt.bak 
	if patch reference-file-after-edit4.txt editY-on-reference-file-after-edit4.patch; \
		then echo "[editY-on-reference-file-after-edit4.patch is applicable, possibly OK \n -> check reference-file-after-edit4-editY.txt to see if it did the right thing]"; \
		else echo '[error: editY-on-reference-file-after-edit4.patch is not applicable]'; \
	fi
	cp reference-file-after-edit4.txt reference-file-after-edit4-editY.txt
	cp reference-file-after-edit4.txt.bak reference-file-after-edit4.txt 

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
	if [ -e reference-file-after-edit2-editX.txt ]; \
		then rm -f reference-file-after-edit2-editX.txt; \
	fi
	if [ -e reference-file-after-edit4-editX.txt ]; \
		then rm -f reference-file-after-edit4-editX.txt; \
	fi
	if [ -e reference-file-after-edit2-editY.txt ]; \
		then rm -f reference-file-after-edit2-editY.txt; \
	fi
	if [ -e reference-file-after-edit4-editY.txt ]; \
		then rm -f reference-file-after-edit4-editY.txt; \
	fi
	
