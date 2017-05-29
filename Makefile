clean: clean_submodules
	rm -f *.pyc

clean_submodules: 
	cd model/ && make clean && cd -
	cd view/ && make clean && cd -
	cd lib/ && make clean && cd -

