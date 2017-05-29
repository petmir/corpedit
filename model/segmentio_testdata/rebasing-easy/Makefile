#TODO
.PHONY: default
default: check_edit1 check_edit2 check_edit3 check_edit4


check_edit1:
	cp cztenten_994-rev0.vert cztenten_994-rev0.vert.bak 
	patch cztenten_994-rev0.vert edit1-on-cztenten_994-rev0.patch 
	if diff cztenten_994-rev0.vert cztenten_994-rev0-after-edit1.txt; \
		then echo '[edit1-on-cztenten_994-rev0.patch OK]'; \
		else echo '[error: edit1-on-cztenten_994-rev0.patch is not correct]'; \
	fi
	cp cztenten_994-rev0.vert.bak cztenten_994-rev0.vert 

clean:
	if [ -e cztenten_994-rev0.vert.bak ]; \
		then cp cztenten_994-rev0.vert.bak cztenten_994-rev0.vert \
		&& rm -f cztenten_994-rev0.vert.bak; \
	fi
	
