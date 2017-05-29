.PHONY: default
default: apply_changelog

apply_changelog:
	cp reference-src-file.txt file.txt
	patch file.txt reference-changelog.patch

clean:
	rm -f file.txt *.index
